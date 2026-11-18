from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.application.services.csv_service import CsvVoxiService
from src.domain.interfaces.arquivo_publisher import ArquivoPublisher
from src.domain.interfaces.clientes_repository import ClientesVoxiRepository
from src.domain.models import ClienteVoxi


@dataclass(frozen=True, slots=True)
class ResultadoProcessamento:
    quantidade_clientes: int
    arquivos: list[Path]
    destinos_publicados: list[str]
    modo_teste: bool


class ProcessarVoxi:
    def __init__(
        self,
        repository: ClientesVoxiRepository,
        csv_service: CsvVoxiService,
        publisher: ArquivoPublisher | None,
    ):
        self.repository = repository
        self.csv_service = csv_service
        self.publisher = publisher

    def executar(
        self,
        *,
        enviar_sftp: bool,
        registrar_processados: bool,
        nome_cedente: str,
        data_execucao: date | None = None,
    ) -> ResultadoProcessamento:
        hoje = data_execucao or date.today()
        clientes = self.repository.listar_elegiveis()
        self._registrar_diagnostico(clientes)
        arquivos = self.csv_service.gerar(clientes, hoje, nome_cedente)

        if not clientes:
            return ResultadoProcessamento(
                0,
                arquivos,
                [],
                not registrar_processados,
            )

        destinos: list[str] = []
        if enviar_sftp:
            if self.publisher is None:
                raise RuntimeError("Publicador SFTP não foi configurado")
            destinos = [
                self.publisher.publicar(arquivo)
                for arquivo in arquivos
            ]

        if registrar_processados:
            self.repository.registrar_processados(clientes)

        return ResultadoProcessamento(
            len(clientes),
            arquivos,
            destinos,
            not registrar_processados,
        )

    @staticmethod
    def _registrar_diagnostico(clientes: list[ClienteVoxi]) -> None:
        logging.debug(
            "Volumes por cedente: %s",
            dict(Counter(cliente.credor for cliente in clientes)),
        )
        for cliente in clientes[:3]:
            logging.debug(
                "Amostra mascarada | credor=%s cpf=%s telefone_final=%s",
                cliente.credor,
                ("*" * max(0, len(cliente.cpf_cnpj) - 4)) + cliente.cpf_cnpj[-4:],
                cliente.telefone[-4:],
            )
