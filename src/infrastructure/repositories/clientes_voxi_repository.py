from __future__ import annotations

import logging
from collections.abc import Callable
from decimal import Decimal
from time import perf_counter

from src.domain.interfaces.clientes_repository import ClientesVoxiRepository
from src.domain.models import CarteiraVoxi, ClienteVoxi
from src.infrastructure.config.settings import montar_config_banco
from src.infrastructure.databases.sql_server import SqlServerConnection


# Contrato que toda procedure do envio ativo precisa devolver. O robô
# procura, entre os result sets da procedure, o primeiro que tenha todas
# estas colunas — assim SELECTs intermediários não atrapalham.
COLUNAS_CONTRATO = frozenset(
    {
        "TELEFONE",
        "CPF_CNPJ",
        "NOME",
        "CREDOR",
        "ID_CLIENTE",
        "ATRASO",
        "SALDO_DEVEDOR",
    }
)

TIMEOUT_PROC_SEGUNDOS = 180


def _conexao_padrao(carteira: CarteiraVoxi) -> SqlServerConnection:
    return SqlServerConnection(
        montar_config_banco(carteira.servidor, carteira.banco)
    )


class SqlClientesVoxiRepository(ClientesVoxiRepository):
    def __init__(
        self,
        conexao_quarentena: SqlServerConnection,
        carteiras: list[CarteiraVoxi],
        conexao_carteira: Callable[[CarteiraVoxi], SqlServerConnection]
        | None = None,
    ):
        # A quarentena é sempre gravada na DAILY_VOXI, que fica em um
        # servidor fixo — independente de onde a procedure da carteira roda.
        self.conexao_quarentena = conexao_quarentena
        self.carteiras = carteiras
        self._conexao_carteira = conexao_carteira or _conexao_padrao

    def listar_elegiveis(self) -> list[ClienteVoxi]:
        registros: list[dict[str, object]] = []
        for carteira in self.carteiras:
            registros.extend(self._executar_procedure(carteira))
        return [self._montar_cliente(registro) for registro in registros]

    def _executar_procedure(
        self, carteira: CarteiraVoxi
    ) -> list[dict[str, object]]:
        started = perf_counter()
        comando = f"EXEC {carteira.proc_qualificada};"
        logging.info(
            "Executando %s para a carteira %s", carteira.origem, carteira.cedente
        )

        with self._conexao_carteira(carteira).conectar() as connection:
            connection.timeout = TIMEOUT_PROC_SEGUNDOS
            cursor = connection.cursor()
            cursor.execute(comando)
            registros = self._ler_result_set_do_contrato(cursor, carteira)

        logging.debug(
            "%s finalizada em %.2fs; %s registros",
            carteira.cedente,
            perf_counter() - started,
            len(registros),
        )
        return registros

    @staticmethod
    def _ler_result_set_do_contrato(
        cursor, carteira: CarteiraVoxi
    ) -> list[dict[str, object]]:
        while True:
            if cursor.description is not None:
                colunas = [str(coluna[0]).upper() for coluna in cursor.description]
                if COLUNAS_CONTRATO.issubset(colunas):
                    return [
                        dict(zip(colunas, linha, strict=True))
                        for linha in cursor.fetchall()
                    ]
            if not cursor.nextset():
                break

        faltando = ", ".join(sorted(COLUNAS_CONTRATO))
        raise RuntimeError(
            f"A procedure {carteira.origem} não devolveu nenhum result set "
            f"com o contrato esperado ({faltando})"
        )

    def registrar_processados(self, clientes: list[ClienteVoxi]) -> None:
        query = """
        INSERT INTO DB_PLANEJAMENTO.dbo.DAILY_VOXI
            (CARTEIRA, CPF, ID_CLIENTE, NM_NOME, ATRASO,
             SALDO_DEVEDOR, TELEFONE, DATA)
        VALUES (?, ?, ?, ?, ?, ?, ?, CONVERT(date, GETDATE()))
        """
        valores = [
            (
                item.credor,
                item.cpf_cnpj,
                item.id_cliente,
                item.nome,
                item.atraso,
                item.saldo_devedor,
                item.telefone,
            )
            for item in clientes
        ]
        with self.conexao_quarentena.conectar() as connection:
            cursor = connection.cursor()
            cursor.fast_executemany = True
            cursor.executemany(query, valores)
            connection.commit()
        logging.debug("%s clientes registrados na DAILY_VOXI", len(clientes))

    @staticmethod
    def _montar_cliente(registro: dict[str, object]) -> ClienteVoxi:
        return ClienteVoxi(
            telefone=str(registro["TELEFONE"]),
            cpf_cnpj=str(registro["CPF_CNPJ"]),
            nome=str(registro["NOME"]),
            credor=str(registro["CREDOR"]),
            id_cliente=int(registro["ID_CLIENTE"]),
            atraso=int(registro["ATRASO"]),
            saldo_devedor=Decimal(str(registro["SALDO_DEVEDOR"])),
        )
