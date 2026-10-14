"""Uso:
  python -m financas import extrato.csv fatura.csv ...
  python -m financas orcamento "Delivery" 150,50      # limite mensal da categoria
  python -m financas pluggy                           # sincroniza com o Meu Pluggy (credenciais no .env)
  python -m financas pluggy --simular                 # idem, numa cópia do banco, sem gravar
  python -m financas backup [--dir PASTA] [--manter N]   # cópia conferida do banco (padrão: backups/, 30 cópias)
  python -m financas restaurar ARQUIVO [--sim]        # volta o banco para um backup (guarda o atual antes)"""
import re
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
            r = pluggy.sincronizar(db.connect())
    except pluggy.ErroPluggy as e:
        print(f"ERRO — {e}")
        return 1
    print(f"Pluggy: {r['lidas']} lidas — {r['novas']} novas, {r['duplicadas']} já existiam"
          f" (CSV ou sincronização anterior); {r['pendentes']} pendentes e {r['ignoradas']} ignoradas")
    return 0


def _aviso_dado_real() -> None:
    print("Atenção: esse arquivo tem seus dados reais. Não coloque no git nem em pasta pública;\n"
          "copie para um disco externo ou uma pasta sincronizada só sua.")


def _backup(args: list[str]) -> int:
    pasta, manter, i = None, backup.MANTER_PADRAO, 0
    try:
        while i < len(args):
            if args[i] == "--dir" and i + 1 < len(args):
                pasta = Path(args[i + 1]); i += 2
            elif args[i] == "--manter" and i + 1 < len(args):
                manter = int(args[i + 1]); i += 2
            else:
                print(__doc__)
                return 2
    except ValueError:
        print("ERRO — --manter precisa de um número inteiro (0 guarda todas)")
        return 1
    try:
        r = backup.fazer(db.DEFAULT_PATH, pasta or backup.pasta_padrao(db.DEFAULT_PATH), manter=manter)
    except backup.ErroBackup as e:
        print(f"ERRO — {e}")
        return 1
    t = r["tabelas"]
    print(f"Backup: {r['arquivo']} ({r['bytes'] / 1024:.0f} KB)")
    print(f"Conferido: integridade ok; {t.get('transactions', 0)} lançamentos, {t.get('rules', 0)} regras, "
          f"{t.get('budgets', 0)} orçamentos")
    if r["removidos"]:
        print(f"Removidas {len(r['removidos'])} cópias antigas (mantidas as {manter} mais novas)")
    _aviso_dado_real()
    return 0


def _restaurar(args: list[str]) -> int:
    arquivos = [a for a in args if not a.startswith("--")]
    if len(arquivos) != 1 or set(args) - {arquivos[0], "--sim"}:
        print(__doc__)
        return 2
    try:
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
    if argv and argv[0] == "restaurar":
        return _restaurar(argv[1:])
    if argv and argv[0] == "pluggy" and set(argv[1:]) <= {"--simular"}:
        return _pluggy(simular="--simular" in argv)
    if argv and argv[0] == "orcamento" and len(argv) == 3:
        return _orcamento(argv[1], argv[2])
    if len(argv) < 2 or argv[0] != "import":
        print(__doc__)
        return 2
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
