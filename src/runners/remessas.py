from __future__ import annotations

import argparse
import logging
import re
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

from src.application.services.zip_remessa_service import ZipRemessaService
from src.domain.models.remessa import CarteiraRemessa
from src.infrastructure.config.settings import (
    ROBO_CARGAS_ROOT, montar_config_banco, obter_config_banco_71,
    obter_config_banco_cargas, obter_config_sftp,
)
from src.infrastructure.databases.sql_server import SqlServerConnection
from src.infrastructure.repositories.origem_remessa_repository import OrigemRemessaRepository
from src.infrastructure.repositories.pi_remessa_repository import PiRemessaRepository
from src.infrastructure.sftp.remessa_publisher import RemessaPublisher
from src.infrastructure.sftp.remessa_source import RemessaSource
from src.shared.logging_config import configurar_logging


ROOT = Path(__file__).resolve().parents[2]
ORIGEM_MU = "/Carga_Mu/Entrada/Carga"
CARTEIRAS = {
    "mu": CarteiraRemessa(
        "mu",
        3,
        "ftp",
        ((r"^REM_CONTRATOS_CHI_\d{8}_\d{6}\.txt$", ""),),
    ),
    "teta_imob": CarteiraRemessa("teta_imob", 99, "sftp", (
        (r"^\d{8}_REMESSA_ARC4U_0755_OUT\.zip$", "remessa"),
        (r"^\d{8}_TELEFONE_0755_OUT\.zip$", "telefone"),
    )),
    "teta_swat": CarteiraRemessa("teta_swat", 84, "sftp", (
        (r"^\d{8}_REMESSA_ARC4U_0753_OUT\.zip$", "remessa"),
        (r"^\d{8}_TELEFONE_0753_OUT\.zip$", "telefone"),
    )),
    "teta_consumer": CarteiraRemessa("teta_consumer", 77, "sftp", (
        (r"^\d{8}_REMESSA_ARC4U_0750_OUT\.zip$", "remessa"),
        (r"^\d{8}_TELEFONE_0750_OUT\.zip$", "telefone"),
    )),
    "beta": CarteiraRemessa("beta", 81, "sftp", (
        (r"^\d{8}_REMESSA_BETA_0751_OUT\.zip$", "remessa"),
        (r"^\d{8}_PARCELAS_BETA_0751_OUT\.zip$", "parcelas"),
    )),
    # O arquivo ZETA nao possui data no nome. A data elegivel e validada
    # pelo horario de modificacao informado pelo SFTP (somente hoje).
    # 376 e o nome atual; 307 e mantido por compatibilidade com o nome
    # anteriormente documentado.
    "zeta": CarteiraRemessa(
        "zeta",
        71,
        "sftp",
        ((r"^C\d+ACME\.TXT\.zip$", ""),),
    ),
    # No PAG, a decisao do dia e feita pelo horario de modificacao retornado
    # pelo SFTP. O nome possui DDMMAAAA, mas nao e usado como controle de envio.
    "pag": CarteiraRemessa(
        "pag",
        43,
        "sftp",
        ((r"^COBRACME\d{8}\.txt$", ""),),
    ),
    # A Nu publica normalmente dois arquivos por dia, podendo publicar
    # mais. Somente nomes iniciados por C sao elegiveis; a data e validada
    # pelo horario de modificacao retornado pelo SFTP.
    "nu": CarteiraRemessa(
        "nu",
        14,
        "sftp",
        ((r"^C.*\.txt$", ""),),
    ),
}


def _ja_enviado(enviados: set[str], carteira: str, tipo: str) -> bool:
    sufixo = f"_{tipo}" if tipo else ""
    base = re.escape(f"remessa_{carteira}{sufixo}")
    data_execucao = date.today().strftime("%Y%m%d")
    padrao = rf"^{base}(?:_\d{{2}})?_{data_execucao}\..+$"
    return any(re.fullmatch(padrao, nome, re.IGNORECASE) for nome in enviados)


def _remessa_pi(
    publicador: RemessaPublisher,
    enviados: set[str],
    dry_run: bool,
) -> None:
    """Gera a remessa da PI por procedure e publica no SFTP VOXI.

    Diferente das demais carteiras: não baixa arquivo de um SFTP de origem;
    roda a proc no .71 e o result set vira o CSV (todas as colunas, sem
    tratamento).
    """
    nome = f"remessa_pi_{date.today():%Y%m%d}.csv"
    if _ja_enviado(enviados, "pi", ""):
        logging.info("JA ENVIADO | carteira=pi | %s | proc dispensada", nome)
        return

    conexao = SqlServerConnection(
        montar_config_banco(obter_config_banco_71().host, "DB_PLANEJAMENTO")
    )
    conteudo = PiRemessaRepository(conexao).gerar_csv()
    logging.info(
        "GERADO (proc) | carteira=pi | arquivo=%s | tamanho=%s bytes",
        nome,
        len(conteudo),
    )

    if dry_run:
        logging.info("NAO TRANSFERIDO (dry-run) | destino=%s", nome)
        return

    destino, transferido = publicador.publicar_bytes(conteudo, nome)
    if transferido:
        logging.info("TRANSFERIDO | destino=%s", destino)
        enviados.add(Path(destino).name)
    else:
        logging.info("JA TRANSFERIDO | destino=%s | mesmo tamanho", destino)


def executar(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Copia remessas das cargas para o SFTP VOXI")
    parser.add_argument(
        "--carteira", choices=["todas", "pi", *CARTEIRAS], default="todas"
    )
    parser.add_argument("--dry-run", action="store_true", help="localiza sem publicar no SFTP VOXI")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)
    configurar_logging(ROOT, args.debug, nome="remessas")
    publicador = RemessaPublisher(obter_config_sftp())
    enviados = publicador.listar_enviados_hoje()
    logging.info("DESTINO VERIFICADO | arquivos_enviados_hoje=%s", len(enviados))
    falhas = []

    # PI: remessa gerada por procedure (nao vem de SFTP de origem)
    if args.carteira in ("todas", "pi"):
        try:
            _remessa_pi(publicador, enviados, args.dry_run)
        except Exception as exc:
            falhas.append("pi")
            logging.error("ERRO | carteira=pi | %s", exc)
    if args.carteira == "pi":
        return 1 if falhas else 0

    selecionadas = (
        CARTEIRAS.values() if args.carteira == "todas"
        else [CARTEIRAS[args.carteira]]
    )
    repositorio = OrigemRemessaRepository(SqlServerConnection(obter_config_banco_cargas()))
    for carteira in selecionadas:
        try:
            origem = repositorio.obter(carteira.id_cedente)
            if carteira.codigo == "mu":
                origem = replace(origem, diretorio=ORIGEM_MU)
            def permitido(nome: str) -> bool:
                corresponde = any(
                    re.fullmatch(padrao, nome, re.IGNORECASE)
                    for padrao, _ in carteira.padroes
                )
                if not corresponde:
                    return False
                if carteira.codigo == "mu":
                    data_d1 = (date.today() - timedelta(days=1)).strftime(
                        "%Y%m%d"
                    )
                    encontrado = re.fullmatch(
                        r"REM_CONTRATOS_CHI_(\d{8})_\d{6}\.txt",
                        nome,
                        re.IGNORECASE,
                    )
                    return bool(encontrado and encontrado.group(1) == data_d1)
                return True
            fonte = RemessaSource(
                origem, carteira.protocolo, ROBO_CARGAS_ROOT / "senhas"
            )
            encontrados = fonte.listar(permitido)
            correspondencias = []
            for indice_origem, nome in enumerate(
                sorted(encontrados, key=str.casefold), start=1
            ):
                for padrao, tipo in carteira.padroes:
                    if re.fullmatch(padrao, nome, re.IGNORECASE):
                        if carteira.codigo == "nu":
                            tipo = f"{indice_origem:02d}"
                        correspondencias.append((nome, tipo))
                        break
            if not correspondencias:
                logging.warning("%s: nenhum arquivo esperado encontrado hoje", carteira.codigo)
                continue
            for nome_origem, tipo in correspondencias:
                if _ja_enviado(enviados, carteira.codigo, tipo):
                    logging.info(
                        "JA ENVIADO | carteira=%s | origem=%s | download dispensado",
                        carteira.codigo,
                        nome_origem,
                    )
                    continue
                logging.info(
                    "ENCONTRADO | carteira=%s | arquivo=%s | iniciando download",
                    carteira.codigo,
                    nome_origem,
                )
                conteudo = fonte.ler(nome_origem)
                logging.info(
                    "DOWNLOAD CONCLUIDO | carteira=%s | arquivo=%s | tamanho=%s bytes",
                    carteira.codigo,
                    nome_origem,
                    len(conteudo),
                )
                arquivos_envio = [(nome_origem, conteudo)]
                if Path(nome_origem).suffix.lower() == ".zip":
                    arquivos_envio = ZipRemessaService.extrair_arquivos(
                        conteudo
                    )
                    logging.info(
                        "DESCOMPACTADO | carteira=%s | zip=%s | arquivos=%s",
                        carteira.codigo,
                        nome_origem,
                        len(arquivos_envio),
                    )

                sufixo = f"_{tipo}" if tipo else ""
                for indice, (nome_interno, conteudo_envio) in enumerate(
                    arquivos_envio, start=1
                ):
                    extensoes = "".join(Path(nome_interno).suffixes)
                    complemento = (
                        f"_{indice:02d}" if len(arquivos_envio) > 1 else ""
                    )
                    novo_nome = (
                        f"remessa_{carteira.codigo}{sufixo}{complemento}_"
                        f"{date.today():%Y%m%d}{extensoes}"
                    )
                    if Path(nome_origem).suffix.lower() == ".zip":
                        logging.info(
                            "ARQUIVO EXTRAIDO | origem=%s | tamanho=%s bytes",
                            nome_interno,
                            len(conteudo_envio),
                        )
                    if args.dry_run:
                        logging.info(
                            "NAO TRANSFERIDO (dry-run) | destino=%s",
                            novo_nome,
                        )
                    else:
                        destino, transferido = publicador.publicar_bytes(
                            conteudo_envio, novo_nome
                        )
                        if transferido:
                            logging.info("TRANSFERIDO | destino=%s", destino)
                            enviados.add(Path(destino).name)
                        else:
                            logging.info(
                                "JA TRANSFERIDO | destino=%s | mesmo tamanho",
                                destino,
                            )
        except Exception as exc:
            falhas.append(carteira.codigo)
            logging.error("ERRO | carteira=%s | %s", carteira.codigo, exc)
    return 1 if falhas else 0
