from __future__ import annotations

from src.domain.models.remessa import OrigemRemessa
from src.infrastructure.databases.sql_server import SqlServerConnection


class OrigemRemessaRepository:
    def __init__(self, connection: SqlServerConnection):
        self.connection = connection

    def obter(self, id_cedente: int) -> OrigemRemessa:
        query = """
            SELECT HOSTNAME, USUARIO, SENHA, PORTA_HOST, ORIGEM_CARGA
            FROM Carga.TB_CONEXAO_SFTP WITH(NOLOCK)
            WHERE ID_CEDENTE = ?
        """
        with self.connection.conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(query, id_cedente)
            row = cursor.fetchone()
        if row is None:
            raise LookupError(f"Credencial de carga nao encontrada: {id_cedente}")
        return OrigemRemessa(
            host=str(row.HOSTNAME).strip(),
            usuario=str(row.USUARIO).strip(),
            senha=str(row.SENHA).strip(),
            porta=int(row.PORTA_HOST),
            diretorio=str(row.ORIGEM_CARGA).strip().replace("\\", "/"),
        )
