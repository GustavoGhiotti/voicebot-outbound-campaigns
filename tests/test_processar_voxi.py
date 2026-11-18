"""CT-09 a CT-15 — regra de negócio do fluxo principal.

A regra mais importante do robô está aqui: a quarentena só pode ser gravada
depois que o upload deu certo. Se isso quebrar, clientes são "queimados"
sem terem sido acionados.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.application.services.csv_service import CsvVoxiService
from src.application.use_cases.processar_voxi import ProcessarVoxi
from tests.dobras import PublisherFake, RepositorioFake, cliente


class TestProcessarVoxi(unittest.TestCase):
    def setUp(self) -> None:
        self._temporario = tempfile.TemporaryDirectory()
        self.csv_service = CsvVoxiService(Path(self._temporario.name))
        self.data = date(2026, 8, 18)
        self.clientes = [
            cliente(id_cliente=1),
            cliente(id_cliente=2, cpf="22222222222"),
        ]

    def tearDown(self) -> None:
        self._temporario.cleanup()

    def _executar(self, repo, publisher, **kwargs):
        return ProcessarVoxi(repo, self.csv_service, publisher).executar(
            data_execucao=self.data, nome_cedente="ZETA", **kwargs
        )

    def test_caminho_feliz_gera_publica_e_registra(self) -> None:
        repo = RepositorioFake(self.clientes)
        publisher = PublisherFake()

        resultado = self._executar(
            repo, publisher, enviar_sftp=True, registrar_processados=True
        )

        self.assertEqual(resultado.quantidade_clientes, 2)
        self.assertEqual(len(resultado.arquivos), 1)
        self.assertEqual(len(resultado.destinos_publicados), 1)
        self.assertEqual(len(publisher.publicados), 1)
        self.assertEqual(len(repo.registrados), 2)
        self.assertFalse(resultado.modo_teste)

    def test_dry_run_gera_arquivo_mas_nao_publica_nem_registra(self) -> None:
        repo = RepositorioFake(self.clientes)

        resultado = self._executar(
            repo, None, enviar_sftp=False, registrar_processados=False
        )

        self.assertEqual(len(resultado.arquivos), 1)
        self.assertEqual(resultado.destinos_publicados, [])
        self.assertEqual(repo.chamadas_registrar, 0)
        self.assertTrue(resultado.modo_teste)

    def test_sem_registro_publica_mas_nao_grava_quarentena(self) -> None:
        repo = RepositorioFake(self.clientes)
        publisher = PublisherFake()

        resultado = self._executar(
            repo, publisher, enviar_sftp=True, registrar_processados=False
        )

        self.assertEqual(len(publisher.publicados), 1)
        self.assertEqual(repo.chamadas_registrar, 0)
        self.assertTrue(resultado.modo_teste)

    def test_falha_no_upload_nao_grava_quarentena(self) -> None:
        """Regra crítica: cliente não enviado não pode ser quarentenado."""
        repo = RepositorioFake(self.clientes)
        publisher = PublisherFake(falhar=True)

        with self.assertRaises(IOError):
            self._executar(
                repo, publisher, enviar_sftp=True, registrar_processados=True
            )

        self.assertEqual(repo.chamadas_registrar, 0)
        self.assertEqual(repo.registrados, [])

    def test_sem_clientes_nao_publica_nem_registra(self) -> None:
        repo = RepositorioFake([])
        publisher = PublisherFake()

        resultado = self._executar(
            repo, publisher, enviar_sftp=True, registrar_processados=True
        )

        self.assertEqual(resultado.quantidade_clientes, 0)
        self.assertEqual(resultado.destinos_publicados, [])
        self.assertEqual(publisher.publicados, [])
        self.assertEqual(repo.chamadas_registrar, 0)

    def test_envio_sem_publisher_configurado_falha_antes_de_registrar(
        self,
    ) -> None:
        repo = RepositorioFake(self.clientes)

        with self.assertRaises(RuntimeError):
            self._executar(
                repo, None, enviar_sftp=True, registrar_processados=True
            )

        self.assertEqual(repo.chamadas_registrar, 0)

    def test_publica_um_unico_arquivo_pelo_cedente(self) -> None:
        repo = RepositorioFake(
            [
                cliente(id_cliente=1),
                cliente(id_cliente=2, cpf="22222222222"),
                cliente(id_cliente=3, cpf="33333333333"),
            ]
        )
        publisher = PublisherFake()

        resultado = self._executar(
            repo, publisher, enviar_sftp=True, registrar_processados=True
        )

        self.assertEqual(len(resultado.arquivos), 1)
        self.assertEqual(len(publisher.publicados), 1)
        self.assertEqual(len(repo.registrados), 3)


if __name__ == "__main__":
    unittest.main()
