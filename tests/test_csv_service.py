"""CT-01 a CT-08 — contrato do arquivo entregue à VOXI.

O formato do CSV é acordo com a discadora: qualquer mudança aqui quebra o
processamento do outro lado.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.application.services.csv_service import CsvVoxiService
from tests.dobras import cliente


class TestCsvVoxiService(unittest.TestCase):
    def setUp(self) -> None:
        self._temporario = tempfile.TemporaryDirectory()
        self.base = Path(self._temporario.name)
        self.service = CsvVoxiService(self.base)
        self.data = date(2026, 8, 18)

    def tearDown(self) -> None:
        self._temporario.cleanup()

    def test_grava_em_subpasta_ano_mes_dia(self) -> None:
        arquivos = self.service.gerar([cliente()], self.data, "ZETA")

        self.assertEqual(len(arquivos), 1)
        self.assertEqual(arquivos[0].parent, self.base / "2026" / "08" / "18")

    def test_nome_do_arquivo_usa_o_cedente_e_a_data(self) -> None:
        arquivos = self.service.gerar([cliente()], self.data, "TETA SWAT")

        self.assertEqual(arquivos[0].name, "TETA_SWAT_20260818.csv")

    def test_conteudo_tem_cabecalho_e_separador_ponto_e_virgula(self) -> None:
        arquivos = self.service.gerar(
            [cliente(telefone="11999998888", cpf="98765432100", nome="MARIA")],
            self.data,
            "ZETA",
        )

        bruto = arquivos[0].read_bytes()
        texto = bruto.decode("utf-8")
        linhas = texto.split("\n")

        self.assertEqual(linhas[0], "TELEFONE;CPF_CNPJ;NOME;CREDOR")
        self.assertEqual(linhas[1], "11999998888;98765432100;MARIA;ZETA")

    def test_arquivo_e_utf8_sem_bom_e_quebra_unix(self) -> None:
        arquivos = self.service.gerar([cliente(nome="JOSÉ ÇA")], self.data, "ZETA")

        bruto = arquivos[0].read_bytes()

        self.assertFalse(bruto.startswith(b"\xef\xbb\xbf"), "não pode ter BOM")
        self.assertNotIn(b"\r\n", bruto, "não pode ter quebra de linha CRLF")
        self.assertIn("JOSÉ ÇA", bruto.decode("utf-8"))

    def test_gera_um_unico_arquivo_nomeado_pelo_cedente(self) -> None:
        clientes = [
            cliente(credor="MU", id_cliente=1),
            cliente(credor="XICLUB", id_cliente=2),
            cliente(credor="MU", id_cliente=3),
        ]

        arquivos = self.service.gerar(clientes, self.data, "MU")

        self.assertEqual(len(arquivos), 1)
        self.assertEqual(arquivos[0].name, "MU_20260818.csv")

    def test_lista_vazia_nao_gera_arquivo(self) -> None:
        arquivos = self.service.gerar([], self.data, "ZETA")

        self.assertEqual(arquivos, [])

    def test_cedente_com_acento_e_simbolo_vira_nome_seguro(self) -> None:
        arquivos = self.service.gerar(
            [cliente()], self.data, "BANCO TETA - IMOBILIÁRIO"
        )

        # Só letras maiúsculas, dígitos e underscore sobrevivem no nome.
        self.assertEqual(arquivos[0].name, "BANCO_TETA_IMOBILI_RIO_20260818.csv")


class TestClienteVoxi(unittest.TestCase):
    def test_para_csv_expoe_somente_as_quatro_colunas_do_contrato(self) -> None:
        linha = cliente().para_csv()

        self.assertEqual(
            list(linha), ["TELEFONE", "CPF_CNPJ", "NOME", "CREDOR"]
        )
        self.assertNotIn("SALDO_DEVEDOR", linha)
        self.assertNotIn("ID_CLIENTE", linha)


if __name__ == "__main__":
    unittest.main()
