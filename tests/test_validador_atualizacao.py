"""CT-44 a CT-52 — trava que impede processar base desatualizada.

Sem esta validação o robô discaria a base do dia anterior sempre que a
carga da DM atrasar. A validação é feita sempre pelo ID_CEDENTE.
"""

from __future__ import annotations

import unittest
from datetime import date, timedelta

from src.infrastructure.databases.atualizacao_carteira import (
    ValidadorAtualizacaoCarteira,
)
from tests.dobras import SqlServerConnectionFake


HOJE = date.today()
ONTEM = HOJE - timedelta(days=1)


class TestValidacaoPorIdDeCedente(unittest.TestCase):
    def test_cedente_atualizado_hoje_passa(self) -> None:
        conexao = SqlServerConnectionFake([(60, HOJE)])

        ValidadorAtualizacaoCarteira(conexao).validar_cedentes([60])

    def test_cedente_desatualizado_bloqueia(self) -> None:
        conexao = SqlServerConnectionFake([(60, ONTEM)])

        with self.assertRaises(RuntimeError) as erro:
            ValidadorAtualizacaoCarteira(conexao).validar_cedentes([60])

        self.assertIn("cedente 60", str(erro.exception))

    def test_cedente_inexistente_na_dm_bloqueia(self) -> None:
        conexao = SqlServerConnectionFake([])

        with self.assertRaises(RuntimeError):
            ValidadorAtualizacaoCarteira(conexao).validar_cedentes([43])

    def test_basta_um_cedente_desatualizado_para_bloquear(self) -> None:
        conexao = SqlServerConnectionFake([(50, HOJE), (51, ONTEM)])

        with self.assertRaises(RuntimeError) as erro:
            ValidadorAtualizacaoCarteira(conexao).validar_cedentes([50, 51])

        self.assertIn("cedente 51", str(erro.exception))

    def test_lista_vazia_e_erro_de_uso(self) -> None:
        conexao = SqlServerConnectionFake([])

        with self.assertRaises(ValueError):
            ValidadorAtualizacaoCarteira(conexao).validar_cedentes([])


if __name__ == "__main__":
    unittest.main()
