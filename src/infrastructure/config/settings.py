from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env")
ROBO_CARGAS_ROOT = Path(os.getenv("ROBO_CARGAS_ROOT", r"C:\Robos\RoboCargas"))
load_dotenv(ROBO_CARGAS_ROOT / ".env")


def _obrigatoria(nome: str) -> str:
    valor = os.getenv(nome, "").strip()
    if not valor:
        raise ValueError(f"Variável obrigatória ausente: {nome}")
    return valor


@dataclass(frozen=True, slots=True)
class DatabaseSettings:
    host: str
    database: str
    user: str
    password: str
    driver: str


@dataclass(frozen=True, slots=True)
class SftpSettings:
    host: str
    port: int
    user: str
    password: str | None
    key_file: Path | None
    remote_dir: str


def obter_config_banco_71() -> DatabaseSettings:
    return DatabaseSettings(
        host=_obrigatoria("DB_HOST"),
        database=os.getenv("DB_NAME", "DB_REPORT"),
        user=_obrigatoria("DB_USER"),
        password=_obrigatoria("DB_PASSWORD"),
        driver=os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
    )


def obter_config_banco_66_logs() -> DatabaseSettings:
    return DatabaseSettings(
        host=os.getenv("LOGS_DB_HOST", "10.0.0.66"),
        database=os.getenv("LOGS_DB_NAME", "LOGS_ROBOS"),
        user=_obrigatoria("DB_USER"),
        password=_obrigatoria("DB_PASSWORD"),
        driver=os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
    )


def obter_config_banco_cadastro() -> DatabaseSettings:
    """Banco onde fica a TB_CARTEIRA_VOXI (cadastro das carteiras)."""
    return DatabaseSettings(
        host=os.getenv("CADASTRO_DB_HOST", "10.0.0.66"),
        database=os.getenv("CADASTRO_DB_NAME", "DB_SFTP"),
        user=_obrigatoria("DB_USER"),
        password=_obrigatoria("DB_PASSWORD"),
        driver=os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
    )


def montar_config_banco(servidor: str, banco: str) -> DatabaseSettings:
    """Conexão para o servidor/banco que a carteira indicar no cadastro.

    Todas as carteiras usam a mesma credencial (DB_USER/DB_PASSWORD): o
    cadastro guarda apenas onde a procedure está, nunca segredo.
    """
    return DatabaseSettings(
        host=servidor,
        database=banco,
        user=_obrigatoria("DB_USER"),
        password=_obrigatoria("DB_PASSWORD"),
        driver=os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
    )


def obter_config_banco_cargas() -> DatabaseSettings:
    return DatabaseSettings(
        host=os.getenv("CARGAS_DB_HOST", os.getenv("DB_66", "10.0.0.66")),
        database=os.getenv("CARGAS_DB_NAME", "DB_DESENVOLVIMENTO"),
        user=os.getenv("CARGAS_DB_USER", _obrigatoria("DB_USER")),
        password=os.getenv(
            "CARGAS_DB_PASSWORD",
            os.getenv("DB_SENHA", _obrigatoria("DB_PASSWORD")),
        ),
        driver=os.getenv("CARGAS_DB_DRIVER", "SQL Server"),
    )


def obter_config_sftp() -> SftpSettings:
    chave = os.getenv("SFTP_KEY_FILE", "").strip()
    return SftpSettings(
        host=_obrigatoria("SFTP_HOST"),
        port=int(os.getenv("SFTP_PORT", "22")),
        user=_obrigatoria("SFTP_USER"),
        password=os.getenv("SFTP_PASSWORD") or None,
        key_file=Path(chave) if chave else None,
        remote_dir=os.getenv("SFTP_REMOTE_DIR", "/entrada").rstrip("/"),
    )


def obter_diretorio_saida() -> Path:
    configurado = Path(
        os.getenv("VOXI_OUTPUT_DIR", r"\\10.0.0.71\d\Automacao\VOXI")
    )
    return configurado if configurado.is_absolute() else ROOT / configurado


# O catálogo de carteiras não fica mais aqui. Ele é lido em tempo de
# execução da tabela DB_SFTP.dbo.TB_CARTEIRA_VOXI, pelo
# SqlCarteirasRepository. Incluir ou remover carteira é INSERT/UPDATE nessa
# tabela, sem alterar código. Ver docs/01-ARQUITETURA.md.
