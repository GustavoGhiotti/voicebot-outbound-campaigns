"""CT-77 a CT-79 — remessa da PI gerada por procedure.

A PI é a única remessa que não vem de um SFTP de origem: roda uma proc no
.71 e o result set vira o CSV, com TODAS as colunas e sem tratamento.
"""

from __future__ import annotations

import unittest

from src.infrastructure.repositories.pi_remessa_repository import (
    PiRemessaRepository,
)
from tests.dobras import SqlServerConnectionProcFake


class TestPiRemessaRepository(unittest.TestCase):
    def test_gera_csv_com_todas_as_colunas_sem_tratamento(self) -> None:
        colunas = ["CPF", "NOME", "VALOR"]
        linhas = [("123", "FULANO", "10.5"), ("456", "CICLANO", None)]
        conexao = SqlServerConnectionProcFake([(colunas, linhas)])

        csv_bytes = PiRemessaRepository(conexao).gerar_csv()
        texto = csv_bytes.decode("utf-8")
        linhas_csv = texto.split("\n")

        self.assertEqual(linhas_csv[0], "CPF;NOME;VALOR")
        self.assertEqual(linhas_csv[1], "123;FULANO;10.5")
        # NULL vira campo vazio, mas a coluna continua lá.
        self.assertEqual(linhas_csv[2], "456;CICLANO;")

    def test_pula_result_sets_sem_retorno(self) -> None:
        conexao = SqlServerConnectionProcFake(
            [(None, []), (["A", "B"], [("1", "2")])]
        )

        csv_bytes = PiRemessaRepository(conexao).gerar_csv()

        self.assertEqual(csv_bytes.decode("utf-8").split("\n")[0], "A;B")

    def test_proc_sem_nenhum_result_set_falha(self) -> None:
        conexao = SqlServerConnectionProcFake([(None, [])])

        with self.assertRaises(RuntimeError):
            PiRemessaRepository(conexao).gerar_csv()


if __name__ == "__main__":
    unittest.main()
