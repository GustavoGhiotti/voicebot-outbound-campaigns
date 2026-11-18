from __future__ import annotations

import io
import zipfile
from pathlib import PurePosixPath


class ZipRemessaService:
    """Extrai arquivos de um ZIP em memoria, sem gravacao local."""

    @staticmethod
    def extrair_arquivos(conteudo_zip: bytes) -> list[tuple[str, bytes]]:
        try:
            with zipfile.ZipFile(io.BytesIO(conteudo_zip), "r") as arquivo_zip:
                arquivos = []
                for item in arquivo_zip.infolist():
                    if item.is_dir():
                        continue
                    nome = PurePosixPath(item.filename.replace("\\", "/")).name
                    if not nome:
                        continue
                    arquivos.append((nome, arquivo_zip.read(item)))
        except zipfile.BadZipFile as exc:
            raise ValueError("arquivo ZIP invalido") from exc

        if not arquivos:
            raise ValueError("nenhum arquivo encontrado dentro do ZIP")
        return arquivos
