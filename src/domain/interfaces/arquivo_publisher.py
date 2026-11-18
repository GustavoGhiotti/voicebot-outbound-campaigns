from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ArquivoPublisher(ABC):
    @abstractmethod
    def publicar(self, arquivo: Path) -> str:
        """Publica um arquivo e retorna seu destino final."""

