"""Dobras de teste (fakes) para substituir banco e SFTP nos testes.

Nenhum teste deste projeto toca em SQL Server, SMB ou SFTP real.
"""

from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path

from src.domain.interfaces.arquivo_publisher import ArquivoPublisher
from src.domain.interfaces.clientes_repository import ClientesVoxiRepository
from src.domain.models import CarteiraVoxi, ClienteVoxi


COLUNAS_CONTRATO = [
    "TELEFONE",
    "CPF_CNPJ",
    "NOME",
    "CREDOR",
    "ID_CLIENTE",
    "ATRASO",
    "SALDO_DEVEDOR",
]


def cliente(
    credor: str = "ZETA",
    cpf: str = "12345678901",
    telefone: str = "11987654321",
    nome: str = "FULANO DE TAL",
    id_cliente: int = 1,
) -> ClienteVoxi:
    """Cria um ClienteVoxi válido, permitindo sobrepor só o que interessa."""
    return ClienteVoxi(
        telefone=telefone,
        cpf_cnpj=cpf,
        nome=nome,
        credor=credor,
        id_cliente=id_cliente,
        atraso=30,
        saldo_devedor=Decimal("1500.55"),
    )


def carteira(
    id_cedente: int = 71,
    cedente: str = "ZETA",
    servidor: str = "10.0.0.71",
    banco: str = "DB_PLANEJAMENTO",
    schema_proc: str = "dbo",
    nome_proc: str = "PRC_VOXI_ZETA",
    valida_carga: bool = True,
) -> CarteiraVoxi:
    return CarteiraVoxi(
        id_cedente=id_cedente,
        cedente=cedente,
        servidor=servidor,
        banco=banco,
        schema_proc=schema_proc,
        nome_proc=nome_proc,
        valida_carga=valida_carga,
    )


def linha_cadastro(
    id_cedente: int = 71,
    cedente: str = "ZETA",
    servidor: str = "10.0.0.71",
    banco: str = "DB_PLANEJAMENTO",
    schema_proc: str = "dbo",
    nome_proc: str = "PRC_VOXI_ZETA",
    valida_carga: bool = True,
) -> tuple:
    """Uma linha da TB_CARTEIRA_VOXI, na ordem em que a query a devolve."""
    return (
        id_cedente,
        cedente,
        servidor,
        banco,
        schema_proc,
        nome_proc,
        valida_carga,
    )


class RepositorioFake(ClientesVoxiRepository):
    def __init__(self, clientes: list[ClienteVoxi]):
        self._clientes = clientes
        self.registrados: list[ClienteVoxi] = []
        self.chamadas_registrar = 0

    def listar_elegiveis(self) -> list[ClienteVoxi]:
        return list(self._clientes)

    def registrar_processados(self, clientes: list[ClienteVoxi]) -> None:
        self.chamadas_registrar += 1
        self.registrados.extend(clientes)


class PublisherFake(ArquivoPublisher):
    def __init__(self, falhar: bool = False):
        self.falhar = falhar
        self.publicados: list[Path] = []

    def publicar(self, arquivo: Path) -> str:
        if self.falhar:
            raise IOError("Falha simulada no upload")
        self.publicados.append(arquivo)
        return f"/remoto/{arquivo.name}"


class CursorFake:
    def __init__(self, linhas: list[tuple]):
        self._linhas = linhas
        self.queries: list[str] = []
        self.parametros: list[object] = []
        self.fast_executemany = False

    def execute(self, query, *args):
        self.queries.append(query)
        self.parametros.append(args)
        return self

    def executemany(self, query, valores):
        self.queries.append(query)
        self.parametros.append(valores)
        return self

    def fetchall(self) -> list[tuple]:
        return self._linhas

    def fetchone(self):
        return self._linhas[0] if self._linhas else None


class ConexaoFake:
    """Substitui o objeto devolvido por SqlServerConnection.conectar()."""

    def __init__(self, linhas: list[tuple]):
        self.timeout = None
        self._cursor = CursorFake(linhas)
        self.commits = 0

    def cursor(self) -> CursorFake:
        return self._cursor

    def commit(self) -> None:
        self.commits += 1


class SqlServerConnectionFake:
    def __init__(self, linhas: list[tuple] | None = None):
        self.conexao = ConexaoFake(linhas or [])

    @contextmanager
    def conectar(self):
        yield self.conexao


# ---------------------------------------------------------------------------
# Execução de procedure: precisa simular vários result sets em sequência
# ---------------------------------------------------------------------------


class CursorProcFake:
    """Cursor com múltiplos result sets, como o de uma stored procedure.

    Cada item de `result_sets` é uma tupla (colunas, linhas). `colunas=None`
    representa um comando sem retorno (ex.: um SELECT ... INTO #TEMP).
    """

    def __init__(self, result_sets: list[tuple[list[str] | None, list[tuple]]]):
        self._sets = list(result_sets) or [(None, [])]
        self._indice = 0
        self.comandos: list[str] = []
        self.parametros: list[object] = []
        self.fast_executemany = False

    @property
    def description(self):
        colunas, _ = self._sets[self._indice]
        if colunas is None:
            return None
        return [(nome,) for nome in colunas]

    def execute(self, comando, *args):
        self.comandos.append(comando)
        self.parametros.append(args)
        return self

    def executemany(self, comando, valores):
        self.comandos.append(comando)
        self.parametros.append(valores)
        return self

    def fetchall(self) -> list[tuple]:
        return self._sets[self._indice][1]

    def nextset(self) -> bool:
        if self._indice + 1 < len(self._sets):
            self._indice += 1
            return True
        return False


class ConexaoProcFake:
    def __init__(self, result_sets):
        self.timeout = None
        self._cursor = CursorProcFake(result_sets)
        self.commits = 0

    def cursor(self) -> CursorProcFake:
        return self._cursor

    def commit(self) -> None:
        self.commits += 1


class SqlServerConnectionProcFake:
    def __init__(self, result_sets=None):
        self.conexao = ConexaoProcFake(result_sets or [])
        self.aberturas = 0

    @contextmanager
    def conectar(self):
        self.aberturas += 1
        yield self.conexao
