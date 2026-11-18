from __future__ import annotations

import posixpath
from datetime import date
from pathlib import Path

import paramiko

from src.domain.interfaces.arquivo_publisher import ArquivoPublisher
from src.infrastructure.config.settings import SftpSettings


class SftpPublisher(ArquivoPublisher):
    def __init__(self, settings: SftpSettings):
        self.settings = settings

    def publicar(self, arquivo: Path) -> str:
        config = self.settings
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        chave = (
            paramiko.RSAKey.from_private_key_file(str(config.key_file))
            if config.key_file else None
        )
        try:
            ssh.connect(
                hostname=config.host,
                port=config.port,
                username=config.user,
                password=config.password,
                pkey=chave,
                look_for_keys=False,
                allow_agent=False,
                timeout=30,
            )
            ssh.get_transport().set_keepalive(7)
            with ssh.open_sftp() as sftp:
                hoje = date.today()
                diretorio_remoto = posixpath.join(
                    config.remote_dir,
                    "ENVIOS_ATIVOS",
                    f"{hoje.year:04d}",
                    f"{hoje.month:02d}",
                    f"{hoje.day:02d}",
                )
                self._garantir_diretorio(sftp, diretorio_remoto)

                remoto = posixpath.join(diretorio_remoto, arquivo.name)
                temporario = remoto + ".part"
                sftp.put(str(arquivo), temporario)
                self._renomear_sobrescrevendo(sftp, temporario, remoto)
                if sftp.stat(remoto).st_size != arquivo.stat().st_size:
                    raise IOError(f"Tamanho divergente após upload: {remoto}")
                return remoto
        finally:
            ssh.close()

    @staticmethod
    def _renomear_sobrescrevendo(
        sftp: paramiko.SFTPClient,
        origem: str,
        destino: str,
    ) -> None:
        """Renomeia sobrescrevendo o destino, se ele já existir.

        O rename padrão do SFTP (CMD_RENAME) falha com 'Failure' quando o
        destino já existe — o que ocorre ao reenviar a mesma carteira no mesmo
        dia. `posix_rename` (extensão do OpenSSH) troca de forma atômica, sem a
        janela em que o arquivo some (mantém a garantia de não entregar arquivo
        pela metade). Se o servidor não tiver a extensão, cai para remover o
        destino e renomear.
        """
        try:
            sftp.posix_rename(origem, destino)
        except IOError:
            try:
                sftp.remove(destino)
            except IOError:
                pass
            sftp.rename(origem, destino)

    @staticmethod
    def _garantir_diretorio(
        sftp: paramiko.SFTPClient,
        diretorio: str,
    ) -> None:
        caminho_atual = "/" if diretorio.startswith("/") else ""
        for parte in diretorio.strip("/").split("/"):
            caminho_atual = posixpath.join(caminho_atual, parte)
            try:
                sftp.stat(caminho_atual)
            except FileNotFoundError:
                sftp.mkdir(caminho_atual)
