from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path


class _SomenteLogDoRobo(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not record.name.startswith(("paramiko", "cryptography"))


def configurar_logging(root: Path, debug: bool, nome: str = "voxi") -> Path:
    pasta = root / "logs"
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / f"{nome}_{date.today():%Y%m%d}.log"
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(arquivo, encoding="utf-8"),
        ],
        force=True,
    )
    # Bibliotecas de infraestrutura geram centenas de linhas de handshake,
    # canais e pacotes quando o modo debug esta ativo. Esses detalhes nao
    # pertencem ao log operacional do robo.
    filtro = _SomenteLogDoRobo()
    for handler in logging.getLogger().handlers:
        handler.addFilter(filtro)
    return arquivo
