from __future__ import annotations

import posixpath

import paramiko

from src.infrastructure.config.settings import SftpSettings
from src.infrastructure.sftp.sftp_publisher import SftpPublisher


class RemessaPublisher(SftpPublisher):
    def listar_enviados_hoje(self) -> set[str]:
        config: SftpSettings = self.settings
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        chave = paramiko.RSAKey.from_private_key_file(str(config.key_file)) if config.key_file else None
        try:
            ssh.connect(
                hostname=config.host, port=config.port, username=config.user,
                password=config.password, pkey=chave, look_for_keys=False,
                allow_agent=False, timeout=30,
            )
            with ssh.open_sftp() as sftp:
                pasta = self._pasta_hoje()
                try:
                    return {
                        nome for nome in sftp.listdir(pasta)
                        if not nome.lower().endswith(".part")
                    }
                except FileNotFoundError:
                    return set()
        finally:
            ssh.close()

    def _pasta_hoje(self) -> str:
        from datetime import date
        hoje = date.today()
        return posixpath.join(
            self.settings.remote_dir, "REMESSA", f"{hoje.year:04d}",
            f"{hoje.month:02d}", f"{hoje.day:02d}",
        )

    def publicar_bytes(self, conteudo: bytes, nome: str) -> tuple[str, bool]:
        config: SftpSettings = self.settings
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        chave = paramiko.RSAKey.from_private_key_file(str(config.key_file)) if config.key_file else None
        try:
            ssh.connect(
                hostname=config.host, port=config.port, username=config.user,
                password=config.password, pkey=chave, look_for_keys=False,
                allow_agent=False, timeout=30,
            )
            with ssh.open_sftp() as sftp:
                pasta = self._pasta_hoje()
                self._garantir_diretorio(sftp, pasta)
                remoto = posixpath.join(pasta, nome)
                try:
                    tamanho_existente = sftp.stat(remoto).st_size
                except FileNotFoundError:
                    tamanho_existente = None
                if tamanho_existente == len(conteudo):
                    return remoto, False
                if tamanho_existente is not None:
                    raise FileExistsError(
                        f"Destino ja existe com tamanho diferente: {remoto}"
                    )
                temporario = remoto + ".part"
                with sftp.open(temporario, "wb") as arquivo:
                    arquivo.write(conteudo)
                sftp.rename(temporario, remoto)
                if sftp.stat(remoto).st_size != len(conteudo):
                    raise IOError(f"Tamanho divergente apos upload: {remoto}")
                return remoto, True
        finally:
            ssh.close()
