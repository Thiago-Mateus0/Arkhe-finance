"""Uso:
  python -m financas import extrato.csv fatura.csv ...
  python -m financas orcamento "Delivery" 150,50      # limite mensal da categoria
  python -m financas pluggy                           # sincroniza com o Meu Pluggy (credenciais no .env)
  python -m financas nuvem import ARQ.csv...          # grava no Postgres hospedado (ADR 0025; precisa do extra nuvem)
  python -m financas pluggy --simular                 # idem, numa cópia do banco, sem gravar
  python -m financas backup [--dir PASTA] [--manter N]   # cópia conferida do banco (padrão: backups/, 30 cópias)
  python -m financas backup --criptografar [--dir PASTA] # idem, com senha (.db.gpg): para pasta na nuvem
  python -m financas restaurar ARQUIVO [--sim]        # volta o banco para um backup (aceita .db.gpg)"""
import getpass
import os
import re
import sqlite3
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

from . import backup, db, service


def _orcamento(categoria: str, valor: str) -> int:
    """Mesma leitura da tela: 150, 150.5, 150,50, 1.500,00 e 1.500 (ponto + 3 dígitos = milhar).
    Negativo ou com mais de 2 casas é recusado, nunca arredondado."""
    txt = valor.strip().replace("R$", "").replace(" ", "")
    if "-" in txt:
        print("ERRO — o limite precisa ser maior que zero")
        return 1
    if "," in txt:
        txt = txt.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", txt):
        txt = txt.replace(".", "")
    try:
        valor_dec = Decimal(txt)
        if valor_dec != valor_dec.quantize(Decimal("0.01")):
            raise ValueError("Use no máximo 2 casas decimais")
        cents = int((valor_dec * 100).to_integral_value())
        conn = db.connect()
        service.set_budget(conn, categoria, cents)
    except (InvalidOperation, ValueError) as e:
        print(f"ERRO — {e}")
        return 1
    print(f"Orçamento de {categoria.strip()}: R$ {cents / 100:.2f} por mês")
    return 0


def _pluggy(simular: bool = False) -> int:
    from . import pluggy
    try:
        if simular:  # roda numa cópia descartável: mostra o resultado sem tocar no banco real
            import shutil
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                copia = Path(tmp) / "simulacao.db"
                if db.DEFAULT_PATH.exists():
                    shutil.copy(db.DEFAULT_PATH, copia)
                conn = db.connect(copia)
                r = pluggy.sincronizar(conn)
                conn.close()
            print("SIMULAÇÃO (nada foi gravado no seu banco):")
        else:
            copia = backup.fazer_automatico(db.DEFAULT_PATH, "antes-de-sincronizar")
            if copia:
                print(f"Backup automático antes de sincronizar: {copia}")
            r = pluggy.sincronizar(db.connect())
    except pluggy.ErroPluggy as e:
        print(f"ERRO — {e}")
        return 1
    print(f"Pluggy: {r['lidas']} lidas — {r['novas']} novas, {r['duplicadas']} já existiam"
          f" (CSV ou sincronização anterior); {r['pendentes']} pendentes e {r['ignoradas']} ignoradas")
    return 0


def _nuvem(args: list[str]) -> int:
    """Grava no Postgres hospedado (ADR 0025): `nuvem import ARQ...` e `nuvem pluggy`."""
    from . import nuvem, pluggy
    if args and args[0] == "migrar" and set(args[1:]) <= {"--simular"}:
        return _migrar_para_nuvem(simular="--simular" in args)
    if not args or args[0] not in ("import", "pluggy") or (args[0] == "import" and len(args) < 2):
        print("uso: python -m financas nuvem import ARQ.csv... | nuvem pluggy | nuvem migrar [--simular]")
        return 2
    try:
        conn = nuvem.connect()
        service.seed_default_rules_once(conn)
        if args[0] == "pluggy":
            r = pluggy.sincronizar(conn)
            print(f"Pluggy (nuvem): {r['lidas']} lidas — {r['novas']} novas, {r['duplicadas']} já existiam")
            return 0
        code = 0
        for name in args[1:]:
            try:
                r = service.import_csv(conn, Path(name).read_bytes())
                print(f"{name}: {r['formato']} — {r['novas']} novas, {r['duplicadas']} duplicadas")
            except (OSError, ValueError) as e:
                print(f"{name}: ERRO — {e}")
                code = 1
        return code
    except (nuvem.ErroNuvem, pluggy.ErroPluggy) as e:
        print(f"ERRO — {e}")
        return 1


def _migrar_para_nuvem(simular: bool) -> int:
    """Copia o banco local (SQLite) para a nuvem, só leitura do local; conferido por totais."""
    from . import nuvem
    if not db.DEFAULT_PATH.exists():
        print(f"ERRO — não achei o banco local em {db.DEFAULT_PATH}")
        return 1
    try:
        nuv = nuvem.connect()
    except nuvem.ErroNuvem as e:
        print(f"ERRO — {e}")
        return 1
    lite = sqlite3.connect(f"file:{db.DEFAULT_PATH}?mode=ro", uri=True)  # leitura: não altera o local
    lite.row_factory = sqlite3.Row
    r = nuvem.migrar(lite, nuv, simular=simular)
    print("SIMULAÇÃO (nada foi gravado na nuvem):" if simular else "Migração para a nuvem:")
    print(f"  lançamentos no banco local: {r['lancamentos_locais']}; novos na nuvem: {r['lancamentos_novos']}")
    print(f"  regras novas: {r['regras_novas']}; nomes próprios: {r['nomes']}; orçamentos: {r['orcamentos']}")
    if not r["conferido"]:
        print("ERRO — os totais da nuvem NÃO batem com os do banco local; nada foi gravado.")
        return 1
    print("  conferido: totais por conta, tipo e categoria iguais aos do banco local")
    return 0


def _aviso_dado_real() -> None:
    print("Atenção: esse arquivo tem seus dados reais. Não coloque no git nem em pasta pública;\n"
          "copie para um disco externo ou uma pasta sincronizada só sua.")


def _ler_senha(confirmar: bool) -> str:
    """Senha digitada (sem aparecer na tela) ou, para agendar, de um arquivo só seu."""
    caminho = os.environ.get("FINANCAS_BACKUP_SENHA_ARQUIVO")
    if caminho:
        p = Path(caminho).expanduser()
        try:
            if p.stat().st_mode & 0o077:
                raise backup.ErroBackup(f"O arquivo de senha {p} está legível por outras pessoas. Rode: chmod 600 {p}")
            return p.read_text(encoding="utf-8").strip()
        except OSError as e:
            raise backup.ErroBackup(f"Não consegui ler o arquivo de senha {p}: {e.strerror}") from e
    if not sys.stdin.isatty():
        raise backup.ErroBackup("Sem terminal para pedir a senha. Para agendar, aponte FINANCAS_BACKUP_SENHA_ARQUIVO.")
    senha = getpass.getpass("Senha do backup: ")
    if confirmar:
        backup.validar_senha(senha)
        if getpass.getpass("Repita a senha: ") != senha:
            raise backup.ErroBackup("As senhas não são iguais. Nada foi feito.")
    return senha


def _backup(args: list[str]) -> int:
    pasta, manter, i, cripto = None, backup.MANTER_PADRAO, 0, False
    try:
        while i < len(args):
            if args[i] == "--criptografar":
                cripto = True; i += 1
            elif args[i] == "--dir" and i + 1 < len(args):
                pasta = Path(args[i + 1]); i += 2
            elif args[i] == "--manter" and i + 1 < len(args):
                manter = int(args[i + 1]); i += 2
            else:
                print(__doc__)
                return 2
    except ValueError:
        print("ERRO — --manter precisa de um número inteiro (0 guarda todas)")
        return 1
    destino = pasta or backup.pasta_padrao(db.DEFAULT_PATH)
    try:
        if cripto:
            if not backup.gpg_disponivel():
                raise backup.ErroBackup("Para criptografar é preciso o gpg. Instale com: sudo apt install gnupg")
            r = backup.fazer_criptografado(db.DEFAULT_PATH, destino, _ler_senha(confirmar=True), manter=manter)
        else:
            r = backup.fazer(db.DEFAULT_PATH, destino, manter=manter)
    except backup.ErroBackup as e:
        print(f"ERRO — {e}")
        return 1
    t = r["tabelas"]
    print(f"Backup{' criptografado' if cripto else ''}: {r['arquivo']} ({r['bytes'] / 1024:.0f} KB)")
    print(f"Conferido: integridade ok; {t.get('transactions', 0)} lançamentos, {t.get('rules', 0)} regras, "
          f"{t.get('budgets', 0)} orçamentos")
    if r["removidos"]:
        print(f"Removidas {len(r['removidos'])} cópias antigas (mantidas as {manter} mais novas)")
    if cripto:
        print("Conferido também: o arquivo abre com a sua senha e dá o mesmo conteúdo.")
        print("Guarde a senha num gerenciador de senhas: sem ela o arquivo não abre, nem por este app.")
        print("Para guardar na nuvem, copie só o arquivo .db.gpg para a pasta sincronizada.")
    else:
        _aviso_dado_real()
    return 0


def _restaurar(args: list[str]) -> int:
    arquivos = [a for a in args if not a.startswith("--")]
    if len(arquivos) != 1 or set(args) - {arquivos[0], "--sim"}:
        print(__doc__)
        return 2
    try:
        if arquivos[0].endswith(".gpg"):
            r = backup.restaurar_criptografado(Path(arquivos[0]), db.DEFAULT_PATH, _ler_senha(confirmar=False),
                                               substituir="--sim" in args)
        else:
            r = backup.restaurar(Path(arquivos[0]), db.DEFAULT_PATH, substituir="--sim" in args)
    except backup.ErroBackup as e:
        print(f"ERRO — {e}")
        return 1
    print(f"Banco restaurado em {r['destino']} ({r['tabelas'].get('transactions', 0)} lançamentos)")
    if r["copia_de_seguranca"]:
        print(f"O banco que estava aqui foi guardado em {r['copia_de_seguranca']}")
    return 0


def main(argv: list[str]) -> int:
    if argv and argv[0] == "backup":
        return _backup(argv[1:])
    if argv and argv[0] == "nuvem":
        return _nuvem(argv[1:])
    if argv and argv[0] == "restaurar":
        return _restaurar(argv[1:])
    if argv and argv[0] == "pluggy" and set(argv[1:]) <= {"--simular"}:
        return _pluggy(simular="--simular" in argv)
    if argv and argv[0] == "orcamento" and len(argv) == 3:
        return _orcamento(argv[1], argv[2])
    if len(argv) < 2 or argv[0] != "import":
        print(__doc__)
        return 2
    copia = backup.fazer_automatico(db.DEFAULT_PATH, "antes-de-importar")
    if copia:
        print(f"Backup automático antes de importar: {copia}")
    conn = db.connect()
    service.seed_default_rules_once(conn)
    code = 0
    for name in argv[1:]:
        try:
            r = service.import_csv(conn, Path(name).read_bytes())
            print(f"{name}: {r['formato']} — {r['novas']} novas, {r['duplicadas']} duplicadas")
        except (OSError, ValueError) as e:
            print(f"{name}: ERRO — {e}")
            code = 1
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
