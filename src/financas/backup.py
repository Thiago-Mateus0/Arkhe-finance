"""Backup e restauração do banco SQLite.

Usa a API de backup do próprio SQLite: a cópia é consistente mesmo com o app aberto, e o arquivo
só aparece com o nome final depois de conferido. Os arquivos têm dado financeiro real: ficam com
permissão só do dono e nunca devem ir para o git (a pasta `backups/` está no .gitignore).
"""
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

PADRAO = re.compile(r"^financas-\d{8}-\d{6}(-\d+)?\.db$")  # só o que o backup automático cria é apagado
MANTER_PADRAO = 30


class ErroBackup(Exception):
    """Mensagem pensada para o dono: diz o que houve e o que fazer."""


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

    `etiqueta` marca cópias de segurança (ex.: antes de restaurar); essas nunca são apagadas sozinhas.
    """
    origem = Path(origem)
    if not origem.is_file():
        raise ErroBackup(f"Não achei o banco em {origem}. Rode o comando na pasta do app ou aponte FINANCAS_DB.")
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)

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
    finally:
        parcial.unlink(missing_ok=True)

    removidos: list[str] = []
    if manter and manter > 0 and not etiqueta:
        antigos = sorted((p for p in pasta.iterdir() if PADRAO.match(p.name)), key=lambda p: p.name, reverse=True)
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
        copia_de_seguranca = fazer(destino, destino.resolve().parent / "backups", etiqueta="antes-da-restauracao",
                                   agora=agora)["arquivo"]

    parcial = destino.with_name(destino.name + ".restaurando")
    try:
        _copiar(arquivo, parcial)
        _conferir(parcial)
        os.replace(parcial, destino)
    finally:
        parcial.unlink(missing_ok=True)
    return {"destino": destino, "tabelas": contagens, "copia_de_seguranca": copia_de_seguranca}
