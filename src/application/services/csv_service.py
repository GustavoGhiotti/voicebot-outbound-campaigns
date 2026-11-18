from __future__ import annotations

import csv
import logging
import re
from datetime import date
from pathlib import Path

from src.domain.models import ClienteVoxi


COLUNAS = ("TELEFONE", "CPF_CNPJ", "NOME", "CREDOR")


class CsvVoxiService:
    def __init__(self, diretorio_base: Path):
        self.diretorio_base = diretorio_base

    def gerar(
        self,
        clientes: list[ClienteVoxi],
        data_execucao: date,
        nome_cedente: str,
    ) -> list[Path]:
        """Gera um único CSV nomeado pelo cedente do cadastro.

        O nome do arquivo vem do ``nome_cedente`` (o CEDENTE cadastrado na
        TB_CARTEIRA_VOXI), não do que a procedure devolve na coluna CREDOR.
        """
        if not clientes:
            return []

        destino = (
            self.diretorio_base
            / f"{data_execucao:%Y}"
            / f"{data_execucao:%m}"
            / f"{data_execucao:%d}"
        )
        destino.mkdir(parents=True, exist_ok=True)
        logging.debug("Diretório de saída validado: %s", destino)

        nome = f"{self._nome_seguro(nome_cedente)}_{data_execucao:%Y%m%d}.csv"
        arquivo = destino / nome
        with arquivo.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=COLUNAS,
                delimiter=";",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(item.para_csv() for item in clientes)
        logging.debug(
            "Arquivo gerado: %s | registros=%s | bytes=%s",
            arquivo,
            len(clientes),
            arquivo.stat().st_size,
        )
        return [arquivo]

    @staticmethod
    def _nome_seguro(valor: str) -> str:
        return re.sub(r"[^A-Z0-9]+", "_", valor.upper()).strip("_")

