from __future__ import annotations

from datetime import date
from pathlib import Path

from src.infrastructure.databases.sql_server import SqlServerConnection


class ControleExecucaoRepository:
    """Persistência do controle diário de produção no SQL Server.

    A chave do dia é ``DATA_REF`` + ``ID_CEDENTE`` + ``CEDENTE``. O
    ``ID_CEDENTE`` (o SFTP/cedente) não é único: carteiras do mesmo grupo o
    compartilham (ex.: Mu, Xiclub e Eta são o cedente 3). Por
    isso o ``CEDENTE`` (nome) entra na chave — assim cada parte é rastreada
    separadamente e uma não bloqueia a outra.
    """

    def __init__(self, connection: SqlServerConnection):
        self.connection = connection

    def concluida(
        self, id_cedente: int, cedente: str, data_execucao: date
    ) -> bool:
        query = """
        SELECT TOP (1) 1
        FROM LOGS_ROBOS.dbo.TB_CONTROLE_EXECUCAO_VOXI WITH (NOLOCK)
        WHERE DATA_REF = ?
          AND ID_CEDENTE = ?
          AND CEDENTE = ?
          AND STATUS = 'CONCLUIDO';
        """
        with self.connection.conectar() as connection:
            cursor = connection.cursor()
            return (
                cursor.execute(query, data_execucao, id_cedente, cedente).fetchone()
                is not None
            )

    def registrar(
        self,
        id_cedente: int,
        cedente: str,
        data_execucao: date,
        quantidade_clientes: int,
        arquivos: list[Path],
    ) -> None:
        nomes_arquivos = ";".join(arquivo.name for arquivo in arquivos) or None
        query = """
        SET XACT_ABORT ON;
        BEGIN TRANSACTION;

        IF EXISTS (
            SELECT 1
            FROM LOGS_ROBOS.dbo.TB_CONTROLE_EXECUCAO_VOXI
                WITH (UPDLOCK, HOLDLOCK)
            WHERE DATA_REF = ?
              AND ID_CEDENTE = ?
              AND CEDENTE = ?
        )
        BEGIN
            UPDATE LOGS_ROBOS.dbo.TB_CONTROLE_EXECUCAO_VOXI
            SET STATUS = 'CONCLUIDO',
                QTD_CLIENTES = ?,
                ARQUIVOS = ?,
                DT_HR_EXECUCAO = SYSDATETIME()
            WHERE DATA_REF = ?
              AND ID_CEDENTE = ?
              AND CEDENTE = ?;
        END
        ELSE
        BEGIN
            INSERT INTO LOGS_ROBOS.dbo.TB_CONTROLE_EXECUCAO_VOXI (
                DATA_REF,
                ID_CEDENTE,
                CEDENTE,
                STATUS,
                QTD_CLIENTES,
                ARQUIVOS,
                DT_HR_EXECUCAO
            )
            VALUES (?, ?, ?, 'CONCLUIDO', ?, ?, SYSDATETIME());
        END;

        COMMIT TRANSACTION;
        """
        parametros = (
            data_execucao,
            id_cedente,
            cedente,
            quantidade_clientes,
            nomes_arquivos,
            data_execucao,
            id_cedente,
            cedente,
            data_execucao,
            id_cedente,
            cedente,
            quantidade_clientes,
            nomes_arquivos,
        )
        with self.connection.conectar() as connection:
            cursor = connection.cursor()
            cursor.execute(query, parametros)
            connection.commit()
