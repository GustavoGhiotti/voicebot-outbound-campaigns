from __future__ import annotations

import logging
from datetime import date

from src.infrastructure.databases.sql_server import SqlServerConnection


class ValidadorAtualizacaoCarteira:
    """Impede o processamento quando a DM do cedente não é do dia."""

    def __init__(self, connection: SqlServerConnection):
        self.connection = connection

    def validar_cedentes(self, ids_cedentes: list[int]) -> None:
        ids = sorted({int(item) for item in ids_cedentes})
        if not ids:
            raise ValueError("Nenhum cedente foi informado para validação")

        placeholders = ", ".join("?" for _ in ids)
        query = f"""
        SELECT
            ID_CEDENTE,
            DT_ATUALIZACAO = MAX(DT_ATUALIZACAO)
        FROM DB_REPORT.DM.TB_CARTEIRA WITH (NOLOCK)
        WHERE STATUS_ATUAL = 1
          AND ID_CEDENTE IN ({placeholders})
        GROUP BY ID_CEDENTE;
        """

        with self.connection.conectar() as connection:
            connection.timeout = 60
            rows = connection.cursor().execute(query, ids).fetchall()

        atualizacoes = {int(row[0]): row[1] for row in rows}
        problemas = [
            f"cedente {id_cedente} (data={atualizacoes.get(id_cedente)})"
            for id_cedente in ids
            if atualizacoes.get(id_cedente) != date.today()
        ]
        if problemas:
            raise RuntimeError(
                "Processamento bloqueado: a DM.TB_CARTEIRA não está "
                "atualizada para hoje. " + " | ".join(problemas)
            )

        logging.info(
            "Validação da DM concluída para o(s) cedente(s) %s em %s",
            ", ".join(str(item) for item in ids),
            date.today().isoformat(),
        )
