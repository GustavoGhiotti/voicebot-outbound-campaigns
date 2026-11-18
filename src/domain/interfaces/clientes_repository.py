from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.models import ClienteVoxi


class ClientesVoxiRepository(ABC):
    @abstractmethod
    def listar_elegiveis(self) -> list[ClienteVoxi]:
        """Lista clientes elegíveis sem alterar o banco."""

    @abstractmethod
    def registrar_processados(self, clientes: list[ClienteVoxi]) -> None:
        """Registra a quarentena após a publicação dos arquivos."""

