"""CT-53 a CT-71 — seleção de carteiras, argumentos da CLI e nome da remessa.

A seleção passou a ser resolvida contra o cadastro TB_CARTEIRA_VOXI, e não
mais contra uma lista fixa no argparse.
"""

from __future__ import annotations

import contextlib
import io
import unittest
from datetime import date

from src.runners.voxi import _argumentos, _carteiras_selecionadas
from src.runners.remessas import CARTEIRAS, _ja_enviado
from tests.dobras import carteira


HOJE = date.today().strftime("%Y%m%d")


@contextlib.contextmanager
def _sem_ruido():
    """Silencia o texto de uso que o argparse escreve ao rejeitar um argumento."""
    with contextlib.redirect_stderr(io.StringIO()):
        yield


def _catalogo() -> dict:
    """Catálogo equivalente ao cadastro atual, chaveado por CEDENTE.

    Mu e Xiclub compartilham o cedente 3 (mesmo SFTP).
    """
    carteiras = [
        carteira(id_cedente=71, cedente="ZETA"),
        carteira(id_cedente=3, cedente="MU"),
        carteira(id_cedente=3, cedente="XICLUB"),
        carteira(id_cedente=43, cedente="RHO"),
    ]
    return {item.cedente: item for item in carteiras}


class TestSelecaoDeCarteiras(unittest.TestCase):
    def setUp(self) -> None:
        self.catalogo = _catalogo()

    def test_todas_devolve_o_cadastro_inteiro(self) -> None:
        self.assertEqual(
            _carteiras_selecionadas("todas", self.catalogo),
            list(self.catalogo.values()),
        )

    def test_selecao_por_id_cedente(self) -> None:
        escolhidas = _carteiras_selecionadas("71", self.catalogo)

        self.assertEqual([item.cedente for item in escolhidas], ["ZETA"])

    def test_id_compartilhado_sobe_todas_as_partes(self) -> None:
        """O cedente 3 sobe Mu e Xiclub juntos."""
        escolhidas = _carteiras_selecionadas("3", self.catalogo)

        self.assertEqual(
            sorted(item.cedente for item in escolhidas), ["MU", "XICLUB"]
        )

    def test_nome_sobe_so_aquela_parte(self) -> None:
        """Reprocessar só o Xiclub não arrasta o resto do cedente 3."""
        escolhidas = _carteiras_selecionadas("xiclub", self.catalogo)

        self.assertEqual([item.cedente for item in escolhidas], ["XICLUB"])

    def test_carteira_fora_do_cadastro_e_recusada(self) -> None:
        with self.assertRaises(ValueError) as erro:
            _carteiras_selecionadas("inexistente", self.catalogo)

        mensagem = str(erro.exception)
        self.assertIn("não está cadastrada", mensagem)
        self.assertIn("ZETA", mensagem)

    def test_carteira_desativada_no_cadastro_some_da_selecao(self) -> None:
        """ATIVO = 0 tira a linha da consulta, então ela nem chega aqui."""
        catalogo = {
            cedente: item
            for cedente, item in self.catalogo.items()
            if cedente != "RHO"
        }

        with self.assertRaises(ValueError):
            _carteiras_selecionadas("rho", catalogo)


class TestArgumentosDaCli(unittest.TestCase):
    def test_padroes_sao_conservadores(self) -> None:
        args = _argumentos([])

        self.assertEqual(args.carteira, "todas")
        self.assertFalse(args.dry_run)
        self.assertFalse(args.debug)
        self.assertFalse(args.sem_registro)
        self.assertFalse(args.ignorar_validacao_carga)

    def test_flags_sao_lidas(self) -> None:
        args = _argumentos(["--carteira", "zeta", "--dry-run", "--debug"])

        self.assertEqual(args.carteira, "zeta")
        self.assertTrue(args.dry_run)
        self.assertTrue(args.debug)

    def test_aceita_qualquer_codigo_e_valida_contra_o_cadastro(self) -> None:
        """A lista fixa saiu do argparse: quem valida é o cadastro."""
        args = _argumentos(["--carteira", "carteira_nova"])

        self.assertEqual(args.carteira, "carteira_nova")

    def test_ignorar_validacao_exige_carteira_especifica(self) -> None:
        """Proteção: não dá para pular a trava da DM em todas as carteiras."""
        with _sem_ruido(), self.assertRaises(SystemExit):
            _argumentos(["--ignorar-validacao-carga"])

    def test_ignorar_validacao_aceito_com_carteira_especifica(self) -> None:
        args = _argumentos(["--carteira", "zeta", "--ignorar-validacao-carga"])

        self.assertTrue(args.ignorar_validacao_carga)


class TestNomeDaRemessa(unittest.TestCase):
    """CT-65 a CT-71 — reconhecimento do que já foi enviado hoje."""

    def test_remessa_do_dia_ja_enviada(self) -> None:
        enviados = {f"remessa_beta_{HOJE}.txt"}

        self.assertTrue(_ja_enviado(enviados, "beta", ""))

    def test_remessa_com_tipo_nao_confunde_com_outro(self) -> None:
        enviados = {f"remessa_beta_parcelas_{HOJE}.zip"}

        self.assertTrue(_ja_enviado(enviados, "beta", "parcelas"))
        self.assertFalse(_ja_enviado(enviados, "beta", "remessa"))

    def test_remessa_numerada_e_reconhecida(self) -> None:
        enviados = {f"remessa_nu_01_{HOJE}.txt"}

        self.assertTrue(_ja_enviado(enviados, "nu", ""))

    def test_remessa_de_outro_dia_nao_conta(self) -> None:
        enviados = {"remessa_beta_20200101.txt"}

        self.assertFalse(_ja_enviado(enviados, "beta", ""))

    def test_destino_vazio_nao_conta(self) -> None:
        self.assertFalse(_ja_enviado(set(), "beta", ""))

    def test_pi_ausente_do_catalogo_de_remessas(self) -> None:
        self.assertNotIn("pi", CARTEIRAS)

    def test_cadastro_das_remessas_e_coerente(self) -> None:
        self.assertTrue(CARTEIRAS)
        for codigo, item in CARTEIRAS.items():
            with self.subTest(codigo=codigo):
                self.assertEqual(item.codigo, codigo)
                self.assertIsInstance(item.id_cedente, int)


if __name__ == "__main__":
    unittest.main()
