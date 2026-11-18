"""CT-72 a CT-76 — controle de execução única por dia.

É o que permite agendar o robô de hora em hora sem enviar a mesma carteira
duas vezes.
"""

from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path

from src.infrastructure.repositories.controle_execucao_repository import (
    ControleExecucaoRepository,
)
from tests.dobras import SqlServerConnectionFake


class TestControleExecucaoRepository(unittest.TestCase):
    def setUp(self) -> None:
        self.data = date(2026, 8, 18)

    def test_carteira_com_registro_e_considerada_concluida(self) -> None:
        conexao = SqlServerConnectionFake([(1,)])

        repo = ControleExecucaoRepository(conexao)

        self.assertTrue(repo.concluida(71, "ZETA", self.data))

    def test_carteira_sem_registro_nao_e_concluida(self) -> None:
        conexao = SqlServerConnectionFake([])

        repo = ControleExecucaoRepository(conexao)

        self.assertFalse(repo.concluida(71, "ZETA", self.data))

    def test_registrar_faz_commit_e_envia_a_chave_diaria(self) -> None:
        conexao = SqlServerConnectionFake([])
        repo = ControleExecucaoRepository(conexao)

        repo.registrar(71, "ZETA", self.data, 250, [Path("ZETA_20260818.csv")])

        self.assertEqual(conexao.conexao.commits, 1)
        parametros = conexao.conexao.cursor().parametros[0][0]
        self.assertIn(self.data, parametros)
        self.assertIn(71, parametros)
        self.assertIn("ZETA", parametros)
        self.assertIn(250, parametros)
        self.assertIn("ZETA_20260818.csv", parametros)

    def test_registrar_junta_varios_arquivos_com_ponto_e_virgula(self) -> None:
        conexao = SqlServerConnectionFake([])
        repo = ControleExecucaoRepository(conexao)

        repo.registrar(
            50,
            "MU",
            self.data,
            300,
            [Path("MU_20260818.csv"), Path("XICLUB_20260818.csv")],
        )

        parametros = conexao.conexao.cursor().parametros[0][0]
        self.assertIn(
            "MU_20260818.csv;XICLUB_20260818.csv", parametros
        )

    def test_registrar_sem_arquivos_grava_nulo(self) -> None:
        conexao = SqlServerConnectionFake([])
        repo = ControleExecucaoRepository(conexao)

        repo.registrar(71, "ZETA", self.data, 0, [])

        parametros = conexao.conexao.cursor().parametros[0][0]
        self.assertIn(None, parametros)


if __name__ == "__main__":
    unittest.main()
