"""CT-31 a CT-43 — execução da procedure e leitura do result set do contrato.

A procedure não recebe parâmetros e pode emitir vários result sets. O robô
precisa achar o result set certo entre eles, e falhar com mensagem clara
quando a procedure não cumprir o contrato.
"""

from __future__ import annotations

import unittest
from decimal import Decimal

from src.infrastructure.repositories.clientes_voxi_repository import (
    SqlClientesVoxiRepository,
)
from tests.dobras import (
    COLUNAS_CONTRATO,
    SqlServerConnectionFake,
    SqlServerConnectionProcFake,
    carteira,
    cliente,
)


LINHA_VALIDA = (
    "11987654321",
    "12345678901",
    "FULANO DE TAL",
    "ZETA",
    77,
    30,
    Decimal("1500.55"),
)


def _repositorio(result_sets, carteiras=None):
    """Monta o repositório com uma conexão de procedure controlada."""
    conexao_proc = SqlServerConnectionProcFake(result_sets)
    conexao_quarentena = SqlServerConnectionFake([])
    repo = SqlClientesVoxiRepository(
        conexao_quarentena,
        carteiras or [carteira()],
        conexao_carteira=lambda _: conexao_proc,
    )
    return repo, conexao_proc, conexao_quarentena


class TestExecucaoDaProcedure(unittest.TestCase):
    def test_monta_o_exec_com_o_nome_qualificado(self) -> None:
        repo, conexao, _ = _repositorio([(COLUNAS_CONTRATO, [LINHA_VALIDA])])

        repo.listar_elegiveis()

        self.assertEqual(
            conexao.conexao.cursor().comandos[0],
            "EXEC [DB_PLANEJAMENTO].[dbo].[PRC_VOXI_ZETA];",
        )

    def test_procedure_e_chamada_sem_parametros(self) -> None:
        """O contrato acordado é procedure sem parâmetro nenhum."""
        repo, conexao, _ = _repositorio([(COLUNAS_CONTRATO, [LINHA_VALIDA])])

        repo.listar_elegiveis()

        self.assertEqual(conexao.conexao.cursor().parametros[0], ())

    def test_converte_a_linha_em_cliente(self) -> None:
        repo, _, _ = _repositorio([(COLUNAS_CONTRATO, [LINHA_VALIDA])])

        clientes = repo.listar_elegiveis()

        self.assertEqual(len(clientes), 1)
        self.assertEqual(clientes[0].telefone, "11987654321")
        self.assertEqual(clientes[0].cpf_cnpj, "12345678901")
        self.assertEqual(clientes[0].credor, "ZETA")
        self.assertEqual(clientes[0].id_cliente, 77)
        self.assertEqual(clientes[0].saldo_devedor, Decimal("1500.55"))

    def test_uma_conexao_por_carteira(self) -> None:
        conexao_proc = SqlServerConnectionProcFake(
            [(COLUNAS_CONTRATO, [LINHA_VALIDA])]
        )
        repo = SqlClientesVoxiRepository(
            SqlServerConnectionFake([]),
            [carteira(id_cedente=71), carteira(id_cedente=84, cedente="TETA SWAT")],
            conexao_carteira=lambda _: conexao_proc,
        )

        repo.listar_elegiveis()

        self.assertEqual(conexao_proc.aberturas, 2)

    def test_procedure_sem_clientes_devolve_lista_vazia(self) -> None:
        repo, _, _ = _repositorio([(COLUNAS_CONTRATO, [])])

        self.assertEqual(repo.listar_elegiveis(), [])


class TestLeituraDoResultSet(unittest.TestCase):
    def test_ignora_result_sets_sem_retorno(self) -> None:
        """SELECT ... INTO #TEMP não devolve colunas e deve ser pulado."""
        repo, _, _ = _repositorio(
            [
                (None, []),
                (None, []),
                (COLUNAS_CONTRATO, [LINHA_VALIDA]),
            ]
        )

        self.assertEqual(len(repo.listar_elegiveis()), 1)

    def test_ignora_result_set_com_colunas_diferentes(self) -> None:
        repo, _, _ = _repositorio(
            [
                (["TOTAL"], [(42,)]),
                (COLUNAS_CONTRATO, [LINHA_VALIDA]),
            ]
        )

        self.assertEqual(len(repo.listar_elegiveis()), 1)

    def test_aceita_colunas_extras_no_result_set(self) -> None:
        colunas = COLUNAS_CONTRATO + ["OBSERVACAO"]
        linha = LINHA_VALIDA + ("qualquer coisa",)
        repo, _, _ = _repositorio([(colunas, [linha])])

        self.assertEqual(len(repo.listar_elegiveis()), 1)

    def test_aceita_colunas_em_minusculo(self) -> None:
        colunas = [nome.lower() for nome in COLUNAS_CONTRATO]
        repo, _, _ = _repositorio([(colunas, [LINHA_VALIDA])])

        self.assertEqual(len(repo.listar_elegiveis()), 1)

    def test_procedure_fora_do_contrato_falha_com_mensagem_util(self) -> None:
        repo, _, _ = _repositorio([(["CPF", "FONE"], [("1", "2")])])

        with self.assertRaises(RuntimeError) as erro:
            repo.listar_elegiveis()

        mensagem = str(erro.exception)
        self.assertIn("PRC_VOXI_ZETA", mensagem)
        self.assertIn("contrato esperado", mensagem)
        self.assertIn("SALDO_DEVEDOR", mensagem)

    def test_procedure_sem_nenhum_retorno_falha(self) -> None:
        repo, _, _ = _repositorio([(None, [])])

        with self.assertRaises(RuntimeError):
            repo.listar_elegiveis()


class TestGravacaoDaQuarentena(unittest.TestCase):
    def test_usa_a_conexao_de_quarentena_e_nao_a_da_procedure(self) -> None:
        """A DAILY_VOXI fica em servidor fixo, não no servidor da carteira."""
        repo, conexao_proc, conexao_quarentena = _repositorio(
            [(COLUNAS_CONTRATO, [LINHA_VALIDA])]
        )

        repo.registrar_processados([cliente()])

        self.assertEqual(conexao_quarentena.conexao.commits, 1)
        self.assertEqual(conexao_proc.aberturas, 0)

    def test_grava_na_daily_voxi(self) -> None:
        repo, _, conexao_quarentena = _repositorio(
            [(COLUNAS_CONTRATO, [LINHA_VALIDA])]
        )

        repo.registrar_processados([cliente(), cliente(id_cliente=2)])

        query = conexao_quarentena.conexao.cursor().queries[0]
        self.assertIn("DB_PLANEJAMENTO.dbo.DAILY_VOXI", query)
        self.assertEqual(len(conexao_quarentena.conexao.cursor().parametros[0]), 2)


if __name__ == "__main__":
    unittest.main()
