from __future__ import annotations

import logging
import re

from src.domain.models import CarteiraVoxi
from src.infrastructure.databases.sql_server import SqlServerConnection


TABELA = "dbo.TB_CARTEIRA_VOXI"

# BANCO, SCHEMA_PROC e NOME_PROC são interpolados no EXEC, então só podem
# conter o que um nome de objeto do SQL Server aceita.
_IDENTIFICADOR = re.compile(r"^[A-Za-z_][A-Za-z0-9_$#]*$")

# SERVIDOR vai para a string de conexão, não para o EXEC. Aceita IP, nome de
# host, instância nomeada (HOST\INSTANCIA) e porta (HOST,1433).
_SERVIDOR = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-]*(\\[A-Za-z0-9._\-]+)?(,\d{1,5})?$")


class SqlCarteirasRepository:
    """Lê o cadastro de carteiras que substituiu o catálogo fixo do código."""

    def __init__(self, connection: SqlServerConnection):
        self.connection = connection

    def listar_ativas(self) -> dict[str, CarteiraVoxi]:
        query = f"""
        SELECT
             ID_CEDENTE
            ,CEDENTE
            ,SERVIDOR
            ,BANCO
            ,SCHEMA_PROC
            ,NOME_PROC
            ,VALIDA_CARGA
        FROM {TABELA} WITH (NOLOCK)
        WHERE ATIVO = 1
        ORDER BY CEDENTE;
        """
        with self.connection.conectar() as connection:
            connection.timeout = 30
            linhas = connection.cursor().execute(query).fetchall()

        # O catálogo é chaveado pelo CEDENTE (nome), que é a identidade da
        # carteira. O ID_CEDENTE NÃO é único: carteiras que compartilham o
        # mesmo SFTP/cedente têm o mesmo id (ex.: Mu, Xiclub e
        # Eta são o cedente 3).
        catalogo: dict[str, CarteiraVoxi] = {}
        for linha in linhas:
            carteira = self._montar(linha)
            if carteira.cedente in catalogo:
                raise RuntimeError(
                    f"{TABELA} tem o CEDENTE '{carteira.cedente}' duplicado"
                )
            catalogo[carteira.cedente] = carteira

        if not catalogo:
            raise RuntimeError(
                f"Nenhuma carteira ativa encontrada em {TABELA}. "
                "Cadastre ao menos uma linha com ATIVO = 1."
            )

        logging.info(
            "Catálogo carregado do cadastro: %s carteira(s) ativa(s) [%s]",
            len(catalogo),
            ", ".join(catalogo),
        )
        return catalogo

    @staticmethod
    def _montar(linha) -> CarteiraVoxi:
        if linha[0] is None:
            raise RuntimeError(
                f"{TABELA}: ID_CEDENTE é obrigatório; sem ele não há como "
                "validar a carga da DM nem identificar a carteira"
            )
        id_cedente = int(linha[0])
        cedente = str(linha[1]).strip().upper()
        servidor = str(linha[2]).strip()
        banco = str(linha[3]).strip()
        schema_proc = str(linha[4]).strip()
        nome_proc = str(linha[5]).strip()
        valida_carga = bool(linha[6]) if linha[6] is not None else True

        if not cedente:
            raise RuntimeError(f"{TABELA}: CEDENTE é obrigatório")

        if not _SERVIDOR.fullmatch(servidor):
            raise RuntimeError(
                f"{TABELA}: SERVIDOR inválido na carteira '{cedente}': "
                f"{servidor!r}"
            )

        for rotulo, valor in (
            ("BANCO", banco),
            ("SCHEMA_PROC", schema_proc),
            ("NOME_PROC", nome_proc),
        ):
            if not _IDENTIFICADOR.fullmatch(valor):
                raise RuntimeError(
                    f"{TABELA}: {rotulo} inválido na carteira '{cedente}': "
                    f"{valor!r}"
                )

        return CarteiraVoxi(
            id_cedente=id_cedente,
            cedente=cedente,
            servidor=servidor,
            banco=banco,
            schema_proc=schema_proc,
            nome_proc=nome_proc,
            valida_carga=valida_carga,
        )
