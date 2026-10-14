"""Backup e restauração do banco SQLite.

Usa a API de backup do próprio SQLite: a cópia é consistente mesmo com o app aberto, e o arquivo
só aparece com o nome final depois de conferido. Os arquivos têm dado financeiro real: ficam com
permissão só do dono e nunca devem ir para o git (a pasta `backups/` está no .gitignore).
"""
import hashlib
import logging
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)

PADRAO = re.compile(r"^financas-\d{8}-\d{6}(-\d+)?\.db$")  # só o que o backup cria é apagado
MANTER_PADRAO = 30
MANTER_AUTO = 10          # cópias "antes-de-..." guardadas
INTERVALO_AUTO = 120      # segundos: vários arquivos importados em sequência geram uma cópia só
SEGURANCA = "antes-da-restauracao"  # nunca é apagada sozinha


def _padrao(etiqueta: str = "") -> re.Pattern:
    marca = re.escape(f"-{etiqueta}") if etiqueta else ""
    return re.compile(rf"^financas-\d{{8}}-\d{{6}}(-\d+)?{marca}\.db$")


class ErroBackup(Exception):
    """Mensagem pensada para o dono: diz o que houve e o que fazer."""


def _erro_de_gravacao(e: OSError, pasta: Path) -> ErroBackup:
    """Traduz falha de disco/permissão em mensagem que diz o que conferir (sem traceback)."""
    if isinstance(e, PermissionError):
        return ErroBackup(
            f"Sem permissão para gravar em {pasta}. Confira o caminho: se for um disco externo, ele precisa estar "
            "espetado e aberto (veja o nome real com `ls /media/$USER`); a pasta tem que ser sua.")
    if getattr(e, "errno", None) == 28:  # ENOSPC
        return ErroBackup(f"Sem espaço em {pasta}. Libere espaço ou escolha outro destino com --dir.")
    return ErroBackup(f"Não consegui gravar o backup em {pasta}: {e.strerror or type(e).__name__}.")


def pasta_padrao(banco: Path) -> Path:
    return Path(os.environ.get("FINANCAS_BACKUP_DIR") or banco.resolve().parent / "backups")


def _contagens(conn: sqlite3.Connection) -> dict[str, int]:
    tabelas = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    return {t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tabelas}


def _conferir(arquivo: Path) -> dict[str, int]:
    """Abre só para leitura, roda a checagem de integridade do SQLite e conta as linhas por tabela."""
    try:
        conn = sqlite3.connect(f"file:{arquivo}?mode=ro", uri=True)
        try:
            if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ErroBackup(f"{arquivo.name}: o arquivo está corrompido (a checagem de integridade falhou).")
            contagens = _contagens(conn)
        finally:
            conn.close()
    except sqlite3.DatabaseError as e:
        raise ErroBackup(f"{arquivo.name} não é um banco válido: {e}") from e
    if "transactions" not in contagens:
        raise ErroBackup(f"{arquivo.name} não parece ser um banco do app (falta a tabela de lançamentos).")
    return contagens


def _copiar(origem: Path, destino: Path) -> None:
    src = sqlite3.connect(f"file:{origem}?mode=ro", uri=True)
    dst = sqlite3.connect(str(destino))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    os.chmod(destino, 0o600)


def fazer(origem: Path, pasta: Path, manter: int | None = MANTER_PADRAO,
          agora: datetime | None = None, etiqueta: str = "") -> dict:
    """Cria `financas-AAAAMMDD-HHMMSS.db` em `pasta`, confere a cópia e apaga as mais antigas.

    `etiqueta` marca cópias feitas por um motivo (ex.: antes de importar). A retenção vale só entre as
    cópias da mesma etiqueta; a de segurança da restauração nunca é apagada sozinha.
    """
    origem = Path(origem)
    if not origem.is_file():
        raise ErroBackup(f"Não achei o banco em {origem}. Rode o comando na pasta do app ou aponte FINANCAS_DB.")
    pasta = Path(pasta)
    try:
        pasta.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise _erro_de_gravacao(e, pasta) from e

    carimbo = (agora or datetime.now()).strftime("%Y%m%d-%H%M%S")
    sufixo = f"-{etiqueta}" if etiqueta else ""
    final, n = pasta / f"financas-{carimbo}{sufixo}.db", 1
    while final.exists():  # duas cópias no mesmo segundo não se sobrescrevem
        final = pasta / f"financas-{carimbo}-{n}{sufixo}.db"
        n += 1
    parcial = final.with_name(final.name + ".parcial")

    try:
        _copiar(origem, parcial)
        contagens = _conferir(parcial)
        os.replace(parcial, final)
    except OSError as e:
        raise _erro_de_gravacao(e, pasta) from e
    finally:
        parcial.unlink(missing_ok=True)

    removidos: list[str] = []
    if manter and manter > 0 and etiqueta != SEGURANCA:
        padrao = _padrao(etiqueta)
        antigos = sorted((p for p in pasta.iterdir() if padrao.match(p.name)), key=lambda p: p.name, reverse=True)
        for velho in antigos[manter:]:
            velho.unlink()
            removidos.append(velho.name)
    return {"arquivo": final, "bytes": final.stat().st_size, "tabelas": contagens, "removidos": removidos}


def restaurar(arquivo: Path, destino: Path, substituir: bool = False, agora: datetime | None = None) -> dict:
    """Troca o banco por um backup. Antes de substituir, guarda uma cópia do banco atual."""
    arquivo, destino = Path(arquivo), Path(destino)
    if not arquivo.is_file():
        raise ErroBackup(f"Não achei o arquivo de backup {arquivo}.")
    contagens = _conferir(arquivo)  # recusa corrompido antes de encostar no banco atual

    copia_de_seguranca = None
    if destino.exists():
        if not substituir:
            raise ErroBackup(
                f"Já existe um banco em {destino}. Para substituí-lo pelo backup, rode de novo com --sim "
                "(uma cópia do banco atual é guardada antes).")
        copia_de_seguranca = fazer(destino, destino.resolve().parent / "backups", manter=None,
                                   etiqueta=SEGURANCA, agora=agora)["arquivo"]

    parcial = destino.with_name(destino.name + ".restaurando")
    try:
        _copiar(arquivo, parcial)
        _conferir(parcial)
        os.replace(parcial, destino)
    except OSError as e:
        raise _erro_de_gravacao(e, destino.parent) from e
    finally:
        parcial.unlink(missing_ok=True)
    return {"destino": destino, "tabelas": contagens, "copia_de_seguranca": copia_de_seguranca}


def fazer_automatico(origem: Path, etiqueta: str, agora: datetime | None = None) -> Path | None:
    """Cópia de segurança antes de uma operação que grava muito (importar, sincronizar).

    Nunca atrapalha a operação: se não der para copiar, registra um aviso (sem dado financeiro) e
    segue. Desligue com FINANCAS_BACKUP_AUTO=0. Devolve o arquivo criado, ou None se não criou.
    """
    if os.environ.get("FINANCAS_BACKUP_AUTO", "1").strip().lower() in ("0", "false", "nao", "não", "no"):
        return None
    origem = Path(origem)
    if not origem.is_file():
        return None  # banco novo: ainda não há o que proteger
    pasta = pasta_padrao(origem)
    agora = agora or datetime.now()
    padrao = _padrao(etiqueta)
    try:
        recentes = [p.stat().st_mtime for p in pasta.iterdir() if padrao.match(p.name)] if pasta.is_dir() else []
        if recentes and agora.timestamp() - max(recentes) < INTERVALO_AUTO:
            return None
        return fazer(origem, pasta, manter=MANTER_AUTO, agora=agora, etiqueta=etiqueta)["arquivo"]
    except (ErroBackup, OSError, sqlite3.Error) as e:
        log.warning("backup automático (%s) não foi feito: %s", etiqueta, type(e).__name__)
        return None


# ---- cópia criptografada (para guardar numa pasta na nuvem) ----
# Usa o GnuPG (criptografia simétrica, AES-256, com checagem de integridade). Escolha deliberada: o
# arquivo abre com `gpg -d` em qualquer computador, mesmo sem este app, e não entra dependência nova.

PADRAO_GPG = re.compile(r"^financas-\d{8}-\d{6}(-\d+)?\.db\.gpg$")
SENHA_MINIMA = 10


def gpg_disponivel() -> bool:
    return shutil.which("gpg") is not None


def validar_senha(senha: str) -> None:
    if len(senha) < SENHA_MINIMA:
        raise ErroBackup(f"Use uma senha de pelo menos {SENHA_MINIMA} caracteres.")


def _gpg(args: list[str], senha: str) -> subprocess.CompletedProcess:
    if not gpg_disponivel():
        raise ErroBackup("Para criptografar é preciso o gpg. Instale com: sudo apt install gnupg")
    # A senha vai pela entrada padrão: não aparece na linha de comando nem na lista de processos.
    return subprocess.run(
        ["gpg", "--batch", "--yes", "--quiet", "--pinentry-mode", "loopback", "--passphrase-fd", "0", *args],
        input=(senha + "\n").encode(), capture_output=True, check=False)


def _sha256(arquivo: Path) -> str:
    h = hashlib.sha256()
    with open(arquivo, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def criptografar(arquivo: Path, destino: Path, senha: str) -> None:
    r = _gpg(["--no-symkey-cache", "--symmetric", "--cipher-algo", "AES256", "--s2k-digest-algo", "SHA512",
              "--s2k-count", "65011712", "-o", str(destino), str(arquivo)], senha)
    if r.returncode != 0:
        raise ErroBackup("Não consegui criptografar o backup (o gpg recusou).")
    os.chmod(destino, 0o600)


def _status_do_gpg(arquivo: Path) -> list[list[str]]:
    try:
        linhas = arquivo.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return [l.split()[1:] for l in linhas if l.startswith("[GNUPG:] ")]


def descriptografar(arquivo: Path, destino: Path, senha: str) -> None:
    """Abre só o que foi **de fato** criptografado com senha e com proteção de integridade.

    O `gpg --decrypt` devolve sucesso também para mensagem OpenPGP sem criptografia (só "dado
    literal"). Quem pudesse trocar o arquivo na nuvem entregaria um banco forjado sem saber a senha.
    Por isso o resultado só vale com os estados do gpg abaixo.
    """
    status = destino.with_name(destino.name + ".status")
    try:
        r = _gpg(["--no-symkey-cache", "--status-file", str(status), "--decrypt", "-o", str(destino), str(arquivo)], senha)
        eventos = _status_do_gpg(status)
    finally:
        status.unlink(missing_ok=True)
    if r.returncode != 0:
        destino.unlink(missing_ok=True)
        raise ErroBackup("Senha incorreta, ou o arquivo está corrompido.")

    nomes = {e[0] for e in eventos if e}
    info = next((e for e in eventos if e and e[0] == "DECRYPTION_INFO"), [])
    aead = len(info) >= 4 and info[3] not in ("0", "")  # DECRYPTION_INFO <mdc> <cifra> <aead>
    protegido = "NEED_PASSPHRASE_SYM" in nomes and "DECRYPTION_OKAY" in nomes and ("GOODMDC" in nomes or aead)
    if not protegido or "ENC_TO" in nomes:
        destino.unlink(missing_ok=True)
        raise ErroBackup("Este arquivo não foi protegido com senha por este app (ou foi trocado). Não vou abrir.")
    os.chmod(destino, 0o600)


def fazer_criptografado(origem: Path, pasta: Path, senha: str, manter: int | None = MANTER_PADRAO,
                        agora: datetime | None = None) -> dict:
    """Backup conferido, criptografado e verificado (abre com a senha e dá o mesmo conteúdo).

    A cópia sem senha existe só numa pasta temporária privada, apagada ao final; só o arquivo
    `.db.gpg` chega à pasta de destino (pode ser uma pasta sincronizada com a nuvem).
    """
    validar_senha(senha)
    pasta = Path(pasta)
    try:
        pasta.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise _erro_de_gravacao(e, pasta) from e
    with tempfile.TemporaryDirectory(prefix="financas-bk-") as tmp:  # 0700, só o dono
        tmp = Path(tmp)
        simples = fazer(origem, tmp, manter=None, agora=agora)
        base = simples["arquivo"].name + ".gpg"
        final, n = pasta / base, 1
        while final.exists():
            final = pasta / base.replace(".db.gpg", f"-{n}.db.gpg")
            n += 1
        parcial = final.with_name(final.name + ".parcial")
        try:
            criptografar(simples["arquivo"], parcial, senha)
            conferencia = tmp / "conferencia.db"
            descriptografar(parcial, conferencia, senha)
            if _sha256(conferencia) != _sha256(simples["arquivo"]):
                raise ErroBackup("A cópia criptografada não bate com o original; nada foi guardado.")
            os.replace(parcial, final)
        except OSError as e:
            raise _erro_de_gravacao(e, pasta) from e
        finally:
            parcial.unlink(missing_ok=True)
        tamanho, tabelas = final.stat().st_size, simples["tabelas"]

    removidos: list[str] = []
    if manter and manter > 0:
        antigos = sorted((p for p in pasta.iterdir() if PADRAO_GPG.match(p.name)), key=lambda p: p.name, reverse=True)
        for velho in antigos[manter:]:
            velho.unlink()
            removidos.append(velho.name)
    return {"arquivo": final, "bytes": tamanho, "tabelas": tabelas, "removidos": removidos}


def restaurar_criptografado(arquivo: Path, destino: Path, senha: str, substituir: bool = False,
                            agora: datetime | None = None) -> dict:
    arquivo = Path(arquivo)
    if not arquivo.is_file():
        raise ErroBackup(f"Não achei o arquivo de backup {arquivo}.")
    with tempfile.TemporaryDirectory(prefix="financas-bk-") as tmp:
        simples = Path(tmp) / "aberto.db"
        descriptografar(arquivo, simples, senha)
        return restaurar(simples, destino, substituir=substituir, agora=agora)
