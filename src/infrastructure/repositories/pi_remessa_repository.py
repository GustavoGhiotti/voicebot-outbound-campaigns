from __future__ import annotations

import csv
import io
import logging

from src.infrastructure.databases.sql_server import SqlServerConnection


# A PI é diferente das outras remessas: em vez de baixar um arquivo do
# SFTP do cedente, ela roda esta procedure fixa no .71 e o result set VIRA a
# remessa. Como é um caso único, a procedure fica direto no código (não no
# cadastro, como o envio ativo).
PROC_PI = "DB_PLANEJAMENTO.[Raw].[BASE_VOXI_PI]"
TIMEOUT_PROC_SEGUNDOS = 180


class PiRemessaRepository:
    """Gera a remessa da PI a partir de uma procedure.

    Envia exatamente o que a procedure devolver — TODAS as colunas, sem
    tratamento, sem filtro de contrato. O que a proc retorna é o que vai no
    arquivo.
    """

    def __init__(self, connection: SqlServerConnection):
        self.connection = connection

    def gerar_csv(self) -> bytes:
        with self.connection.conectar() as connection:
            connection.timeout = TIMEOUT_PROC_SEGUNDOS
            cursor = connection.cursor()
            cursor.execute(f"EXEC {PROC_PI};")
            colunas, linhas = self._primeiro_result_set(cursor)

        logging.info(
            "PI: procedure devolveu %s coluna(s) e %s linha(s)",
            len(colunas),
            len(linhas),
        )

        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
        writer.writerow(colunas)
        writer.writerows(linhas)
        return buffer.getvalue().encode("utf-8")

    @staticmethod
    def _primeiro_result_set(cursor) -> tuple[list[str], list[list[str]]]:
        """Pega o primeiro result set com colunas, pulando comandos sem retorno."""
        while True:
            if cursor.description is not None:
                colunas = [str(coluna[0]) for coluna in cursor.description]
                linhas = [
                    ["" if valor is None else str(valor) for valor in linha]
                    for linha in cursor.fetchall()
                ]
                return colunas, linhas
            if not cursor.nextset():
                break
        raise RuntimeError(
            f"A procedure {PROC_PI} não devolveu nenhum result set"
        )
