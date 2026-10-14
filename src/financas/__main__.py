"""Uso:
  python -m financas import extrato.csv fatura.csv ...
  python -m financas orcamento "Delivery" 150,50      # limite mensal da categoria
  python -m financas pluggy                           # sincroniza com o Meu Pluggy (credenciais no .env)
  python -m financas pluggy --simular                 # idem, numa cópia do banco, sem gravar"""
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

from . import db, service


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


def main(argv: list[str]) -> int:
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
