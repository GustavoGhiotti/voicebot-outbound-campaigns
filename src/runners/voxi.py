from __future__ import annotations

import argparse
import logging
import traceback
from datetime import date
from pathlib import Path

from src.application.services.csv_service import CsvVoxiService
from src.application.use_cases.processar_voxi import (
    ProcessarVoxi,
    ResultadoProcessamento,
)
from src.domain.models import CarteiraVoxi
from src.infrastructure.config.settings import (
    obter_config_banco_66_logs,
    obter_config_banco_71,
    obter_config_banco_cadastro,
    obter_config_sftp,
    obter_diretorio_saida,
)
from src.infrastructure.databases.atualizacao_carteira import (
    ValidadorAtualizacaoCarteira,
)
from src.infrastructure.databases.sql_server import SqlServerConnection
from src.infrastructure.repositories.carteiras_repository import (
    SqlCarteirasRepository,
)
from src.infrastructure.repositories.clientes_voxi_repository import (
    SqlClientesVoxiRepository,
)
from src.infrastructure.repositories.controle_execucao_repository import (
    ControleExecucaoRepository,
)
from src.infrastructure.sftp.sftp_publisher import SftpPublisher
from src.shared.logging_config import configurar_logging


ROOT = Path(__file__).resolve().parents[2]


def executar(argv: list[str] | None = None) -> int:
    args = _argumentos(argv)
    log_file = configurar_logging(ROOT, args.debug)
    logging.info(
        "Início VOXI | debug=%s | dry_run=%s | sem_registro=%s | "
        "ignorar_validacao_carga=%s",
        args.debug,
        args.dry_run,
        args.sem_registro,
        args.ignorar_validacao_carga,
    )
    logging.info("Log da execução: %s", log_file)

    try:
        return _executar_carteiras_reais(args)
    except Exception:
        logging.error("Falha na execução VOXI\n%s", traceback.format_exc())
        return 1


def _executar_carteiras_reais(args: argparse.Namespace) -> int:
    catalogo = SqlCarteirasRepository(
        SqlServerConnection(obter_config_banco_cadastro())
    ).listar_ativas()
    carteiras = _carteiras_selecionadas(args.carteira, catalogo)
    connection = SqlServerConnection(obter_config_banco_71())
    validador = ValidadorAtualizacaoCarteira(connection)
    diretorio_saida = obter_diretorio_saida()
    csv_service = CsvVoxiService(diretorio_saida)
    publisher = None if args.dry_run else SftpPublisher(obter_config_sftp())
    enviar_sftp = not args.dry_run
    registrar_processados = enviar_sftp and not args.sem_registro
    producao = enviar_sftp and registrar_processados
    hoje = date.today()
    controle = ControleExecucaoRepository(
        SqlServerConnection(obter_config_banco_66_logs())
    )
    falhas: list[str] = []
    processadas = 0
    pendentes_atualizacao = 0
    pendentes_sem_clientes = 0
    ja_concluidas = 0
    # Um ID_CEDENTE (SFTP) é validado na DM uma única vez por rodada, mesmo
    # que várias carteiras o compartilhem (ex.: Mu trio = cedente 3).
    # None = validado e ok; str = motivo do bloqueio.
    validacao_carga: dict[int, str | None] = {}

    for carteira in carteiras:
        if producao and controle.concluida(
            carteira.id_cedente, carteira.cedente, hoje
        ):
            ja_concluidas += 1
            logging.info(
                "%s ignorada: produção já concluída hoje",
                carteira.cedente,
            )
            continue

        if args.ignorar_validacao_carga:
            logging.warning(
                "%s: validação de carga processada na DM.TB_CARTEIRA "
                "foi ignorada manualmente",
                carteira.cedente,
            )
        elif not carteira.valida_carga:
            logging.info(
                "%s: não valida carga na DM (VALIDA_CARGA = 0 no cadastro)",
                carteira.cedente,
            )
        else:
            if carteira.id_cedente not in validacao_carga:
                try:
                    validador.validar_cedentes([carteira.id_cedente])
                    validacao_carga[carteira.id_cedente] = None
                except RuntimeError as exc:
                    validacao_carga[carteira.id_cedente] = str(exc)
            motivo = validacao_carga[carteira.id_cedente]
            if motivo is not None:
                pendentes_atualizacao += 1
                logging.warning("%s pendente: %s", carteira.cedente, motivo)
                continue

        try:
            resultado = ProcessarVoxi(
                SqlClientesVoxiRepository(connection, [carteira]),
                csv_service,
                publisher,
            ).executar(
                enviar_sftp=enviar_sftp,
                registrar_processados=registrar_processados,
                nome_cedente=carteira.cedente,
                data_execucao=hoje,
            )
            _registrar_resultado(carteira.cedente, resultado)
            if resultado.quantidade_clientes == 0:
                pendentes_sem_clientes += 1
                logging.warning(
                    "%s pendente: a procedure não retornou clientes; "
                    "execução não será registrada como concluída",
                    carteira.cedente,
                )
                continue
            if producao:
                if not resultado.arquivos or not resultado.destinos_publicados:
                    raise RuntimeError(
                        "Processamento produziu clientes, mas não confirmou "
                        "arquivo gerado e publicação no SFTP"
                    )
                controle.registrar(
                    carteira.id_cedente,
                    carteira.cedente,
                    hoje,
                    resultado.quantidade_clientes,
                    resultado.arquivos,
                )
                logging.info(
                    "%s registrada como concluída hoje no banco",
                    carteira.cedente,
                )
            processadas += 1
        except Exception:
            falhas.append(carteira.cedente)
            logging.error(
                "Falha ao processar %s\n%s",
                carteira.cedente,
                traceback.format_exc(),
            )

    logging.info(
        "Resumo da rodada: processadas=%s já_concluídas=%s "
        "aguardando_atualização=%s sem_clientes=%s falhas=%s",
        processadas,
        ja_concluidas,
        pendentes_atualizacao,
        pendentes_sem_clientes,
        falhas,
    )
    return 1 if falhas else 0


def _carteiras_selecionadas(
    selecao: str,
    catalogo: dict[str, CarteiraVoxi],
) -> list[CarteiraVoxi]:
    """Resolve o argumento --carteira contra o cadastro.

    'todas' sobe o catálogo inteiro. Caso contrário, casa o valor contra o
    ID_CEDENTE (número) ou o nome do cedente (sem diferenciar maiúsculas).
    Um ID_CEDENTE compartilhado sobe todas as suas partes (ex.: '3' sobe
    Mu, Xiclub e Eta); um nome sobe só aquela carteira.
    """
    if selecao == "todas":
        return list(catalogo.values())

    alvo = selecao.strip()
    escolhidas = [
        item
        for item in catalogo.values()
        if str(item.id_cedente) == alvo or item.cedente == alvo.upper()
    ]
    if escolhidas:
        return escolhidas

    disponiveis = ", ".join(
        f"{item.id_cedente} ({item.cedente})" for item in catalogo.values()
    )
    raise ValueError(
        f"Carteira '{selecao}' não está cadastrada e ativa em "
        f"TB_CARTEIRA_VOXI. Disponíveis: todas, {disponiveis}"
    )


def _registrar_resultado(
    rotulo: str,
    resultado: ResultadoProcessamento,
) -> None:
    for arquivo in resultado.arquivos:
        logging.info("Gerado %s (%s bytes)", arquivo, arquivo.stat().st_size)
    for destino in resultado.destinos_publicados:
        logging.info("Publicado em %s", destino)
    logging.info(
        "%s concluída: clientes=%s arquivos=%s modo_teste=%s",
        rotulo,
        resultado.quantidade_clientes,
        len(resultado.arquivos),
        resultado.modo_teste,
    )


def _argumentos(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera e envia os mailings VOXI")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="não envia nem grava DAILY_VOXI",
    )
    parser.add_argument("--debug", action="store_true", help="ativa logs detalhados")
    parser.add_argument(
        "--sem-registro",
        action="store_true",
        help="envia ao SFTP, mas não grava na DAILY_VOXI",
    )
    parser.add_argument(
        "--ignorar-validacao-carga",
        action="store_true",
        help=(
            "permite processar uma carteira específica sem validar se a "
            "carga foi atualizada hoje na DM.TB_CARTEIRA"
        ),
    )
    parser.add_argument(
        "--carteira",
        default="todas",
        help=(
            "ID_CEDENTE ou nome do cedente cadastrado em TB_CARTEIRA_VOXI, "
            "ou 'todas'. A validação é feita contra o cadastro, na execução"
        ),
    )
    args = parser.parse_args(argv)
    if args.ignorar_validacao_carga and args.carteira == "todas":
        parser.error("--ignorar-validacao-carga exige uma carteira específica")
    return args
