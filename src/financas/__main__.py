"""Uso: python -m financas import extrato.csv fatura.csv ..."""
import sys
from pathlib import Path

from . import db, service


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] != "import":
        print(__doc__)
        return 2
    conn = db.connect()
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
