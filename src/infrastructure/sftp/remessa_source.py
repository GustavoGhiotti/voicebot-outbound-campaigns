from __future__ import annotations

import ftplib
import io
import posixpath
import stat
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path

import paramiko

from src.domain.models.remessa import OrigemRemessa


class RemessaSource:
    def __init__(self, origem: OrigemRemessa, protocolo: str, chaves_dir: Path):
        self.origem = origem
        self.protocolo = protocolo
        self.chaves_dir = chaves_dir

    def listar(self, permitido: Callable[[str], bool]) -> list[str]:
        if self.protocolo == "ftp":
            return self._listar_ftp(permitido)
        return self._listar_sftp(permitido)

    def ler(self, nome: str) -> bytes:
        if self.protocolo == "ftp":
            return self._ler_ftp(nome)
        return self._ler_sftp(nome)

    def _conectar_sftp(self) -> paramiko.SSHClient:
        origem = self.origem
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        key_path = self.chaves_dir / origem.senha
        pkey = None
        password = origem.senha
        if key_path.is_file():
            pkey = paramiko.RSAKey.from_private_key_file(str(key_path))
            password = None
        ssh.connect(
            hostname=origem.host, port=origem.porta,
            username=origem.usuario, password=password, pkey=pkey,
            look_for_keys=False, allow_agent=False, timeout=30,
        )
        ssh.get_transport().set_keepalive(7)
        return ssh

    def _listar_sftp(self, permitido: Callable[[str], bool]) -> list[str]:
        ssh = self._conectar_sftp()
        try:
            with ssh.open_sftp() as sftp:
                itens = sftp.listdir_attr(self.origem.diretorio)
                return [
                    item.filename for item in itens
                    if stat.S_ISREG(item.st_mode)
                    and datetime.fromtimestamp(item.st_mtime).date() == date.today()
                    and permitido(item.filename)
                ]
        finally:
            ssh.close()

    def _ler_sftp(self, nome: str) -> bytes:
        ssh = self._conectar_sftp()
        try:
            with ssh.open_sftp() as sftp:
                with sftp.open(posixpath.join(self.origem.diretorio, nome), "rb") as arquivo:
                    return arquivo.read()
        finally:
            ssh.close()

    def _conectar_ftp(self) -> ftplib.FTP:
        origem = self.origem
        ftp = ftplib.FTP()
        ftp.connect(origem.host, origem.porta, timeout=30)
        ftp.login(origem.usuario, origem.senha)
        ftp.cwd(origem.diretorio)
        return ftp

    def _listar_ftp(self, permitido: Callable[[str], bool]) -> list[str]:
        ftp = self._conectar_ftp()
        try:
            resultado = []
            for nome in ftp.nlst():
                nome = Path(nome).name
                if not permitido(nome):
                    continue
                try:
                    modificado = datetime.strptime(
                        ftp.sendcmd(f"MDTM {nome}")[4:].split(".")[0], "%Y%m%d%H%M%S"
                    ).date()
                except (ValueError, ftplib.error_perm):
                    continue
                if modificado != date.today():
                    continue
                resultado.append(Path(nome).name)
            return resultado
        finally:
            try:
                ftp.quit()
            except ftplib.all_errors:
                ftp.close()

    def _ler_ftp(self, nome: str) -> bytes:
        ftp = self._conectar_ftp()
        try:
            buffer = io.BytesIO()
            ftp.retrbinary(f"RETR {nome}", buffer.write)
            return buffer.getvalue()
        finally:
            try:
                ftp.quit()
            except ftplib.all_errors:
                ftp.close()
