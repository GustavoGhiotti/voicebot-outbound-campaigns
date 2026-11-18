"""CT-16 a CT-30 — leitura do cadastro TB_CARTEIRA_VOXI.

O cadastro substituiu o catálogo que ficava fixo no settings.py. Como agora
qualquer pessoa com acesso ao banco pode incluir uma carteira, o repositório
precisa rejeitar linha malformada em vez de deixar o erro aparecer só na
hora do EXEC.
"""

from __future__ import annotations

import unittest

from src.infrastructure.repositories.carteiras_repository import (
    SqlCarteirasRepository,
)
from tests.dobras import SqlServerConnectionFake, linha_cadastro


class TestLeituraDoCadastro(unittest.TestCase):
    def _catalogo(self, linhas):
        return SqlCarteirasRepository(
            SqlServerConnectionFake(linhas)
        ).listar_ativas()

    def test_monta_a_carteira_a_partir_da_linha(self) -> None:
        catalogo = self._catalogo([linha_cadastro()])

        carteira = catalogo["ZETA"]
        self.assertEqual(carteira.id_cedente, 71)
        self.assertEqual(carteira.cedente, "ZETA")
        self.assertEqual(carteira.servidor, "10.0.0.71")
        self.assertEqual(carteira.banco, "DB_PLANEJAMENTO")
        self.assertEqual(carteira.schema_proc, "dbo")
        self.assertEqual(carteira.nome_proc, "PRC_VOXI_ZETA")

    def test_preserva_a_ordem_do_cadastro(self) -> None:
        catalogo = self._catalogo(
            [
                linha_cadastro(id_cedente=71, cedente="ZETA"),
                linha_cadastro(id_cedente=84, cedente="TETA SWAT"),
                linha_cadastro(id_cedente=81, cedente="BANCO BETA"),
            ]
        )

        self.assertEqual(list(catalogo), ["ZETA", "TETA SWAT", "BANCO BETA"])

    def test_id_cedente_compartilhado_e_permitido(self) -> None:
        """Mu, Xiclub e Eta são o mesmo cedente (3)."""
        catalogo = self._catalogo(
            [
                linha_cadastro(id_cedente=3, cedente="MU"),
                linha_cadastro(id_cedente=3, cedente="XICLUB"),
                linha_cadastro(id_cedente=3, cedente="ETA"),
            ]
        )

        self.assertEqual(len(catalogo), 3)
        self.assertEqual(catalogo["XICLUB"].id_cedente, 3)
        self.assertEqual(catalogo["ETA"].id_cedente, 3)

    def test_cedente_vem_sempre_em_maiusculo(self) -> None:
        catalogo = self._catalogo([linha_cadastro(cedente="zeta")])

        self.assertEqual(catalogo["ZETA"].cedente, "ZETA")

    def test_valida_carga_e_lido_do_cadastro(self) -> None:
        catalogo = self._catalogo(
            [
                linha_cadastro(cedente="ZETA", valida_carga=False),
                linha_cadastro(cedente="RHO", id_cedente=43, valida_carga=True),
            ]
        )

        self.assertFalse(catalogo["ZETA"].valida_carga)
        self.assertTrue(catalogo["RHO"].valida_carga)

    def test_espaco_em_branco_e_removido(self) -> None:
        catalogo = self._catalogo([linha_cadastro(cedente="  zeta  ")])

        self.assertIn("ZETA", catalogo)
        self.assertEqual(catalogo["ZETA"].cedente, "ZETA")

    def test_query_filtra_somente_carteiras_ativas(self) -> None:
        conexao = SqlServerConnectionFake([linha_cadastro()])

        SqlCarteirasRepository(conexao).listar_ativas()

        query = conexao.conexao.cursor().queries[0]
        self.assertIn("ATIVO = 1", query)
        self.assertIn("ORDER BY CEDENTE", query)


class TestValidacaoDoCadastro(unittest.TestCase):
    def _listar(self, linhas):
        return SqlCarteirasRepository(
            SqlServerConnectionFake(linhas)
        ).listar_ativas()

    def test_cadastro_vazio_e_erro_claro(self) -> None:
        with self.assertRaises(RuntimeError) as erro:
            self._listar([])

        self.assertIn("Nenhuma carteira ativa", str(erro.exception))

    def test_cedente_duplicado_e_recusado(self) -> None:
        with self.assertRaises(RuntimeError) as erro:
            self._listar([linha_cadastro(), linha_cadastro()])

        self.assertIn("duplicado", str(erro.exception))

    def test_sem_id_cedente_e_recusado(self) -> None:
        """Sem ID_CEDENTE não há como validar a carga da DM nem identificar."""
        with self.assertRaises(RuntimeError) as erro:
            self._listar([linha_cadastro(id_cedente=None)])

        self.assertIn("ID_CEDENTE", str(erro.exception))

    def test_nome_de_procedure_com_injecao_e_recusado(self) -> None:
        """O nome vai interpolado no EXEC: não pode aceitar qualquer coisa."""
        with self.assertRaises(RuntimeError) as erro:
            self._listar(
                [linha_cadastro(nome_proc="PRC_X]; DROP TABLE ALVO; --")]
            )

        self.assertIn("NOME_PROC", str(erro.exception))

    def test_banco_e_schema_tambem_sao_validados(self) -> None:
        for campo in ("banco", "schema_proc"):
            with self.subTest(campo=campo):
                with self.assertRaises(RuntimeError):
                    self._listar([linha_cadastro(**{campo: "x];--"})])

    def test_servidor_aceita_ip_host_instancia_e_porta(self) -> None:
        for servidor in (
            "10.0.0.71",
            "SRVSQL01",
            "srvsql01.grupoacme.local",
            "SRVSQL01\\PROD",
            "10.0.0.71,1433",
        ):
            with self.subTest(servidor=servidor):
                catalogo = self._listar([linha_cadastro(servidor=servidor)])
                self.assertEqual(catalogo["ZETA"].servidor, servidor)

    def test_servidor_com_injecao_e_recusado(self) -> None:
        with self.assertRaises(RuntimeError) as erro:
            self._listar([linha_cadastro(servidor="1.2.3.4; DROP TABLE X")])

        self.assertIn("SERVIDOR", str(erro.exception))

    def test_cedente_vazio_e_recusado(self) -> None:
        with self.assertRaises(RuntimeError) as erro:
            self._listar([linha_cadastro(cedente="   ")])

        self.assertIn("obrigatório", str(erro.exception))


class TestNomeQualificadoDaProcedure(unittest.TestCase):
    def test_monta_o_nome_com_colchetes(self) -> None:
        catalogo = SqlCarteirasRepository(
            SqlServerConnectionFake([linha_cadastro()])
        ).listar_ativas()

        self.assertEqual(
            catalogo["ZETA"].proc_qualificada,
            "[DB_PLANEJAMENTO].[dbo].[PRC_VOXI_ZETA]",
        )

    def test_origem_e_legivel_para_log(self) -> None:
        catalogo = SqlCarteirasRepository(
            SqlServerConnectionFake([linha_cadastro()])
        ).listar_ativas()

        self.assertEqual(
            catalogo["ZETA"].origem,
            "10.0.0.71/DB_PLANEJAMENTO.dbo.PRC_VOXI_ZETA",
        )


if __name__ == "__main__":
    unittest.main()
