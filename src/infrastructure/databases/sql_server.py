from __future__ import annotations

from contextlib import contextmanager

import pyodbc

from src.infrastructure.config.settings import DatabaseSettings


class SqlServerConnection:
    def __init__(self, settings: DatabaseSettings):
        self.settings = settings

    @contextmanager
    def conectar(self):
        config = self.settings
        connection = pyodbc.connect(
            f"DRIVER={{{config.driver}}};SERVER={config.host};"
            f"DATABASE={config.database};UID={config.user};PWD={config.password};"
            "TrustServerCertificate=YES;",
            timeout=30,
        )
        try:
            yield connection
        finally:
            connection.close()
