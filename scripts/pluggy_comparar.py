"""Compara o Meu Pluggy com o banco local (importado por CSV) e imprime SÓ CONTAGENS.

Serve para decidir como casar os lançamentos do Pluggy com os do CSV sem contar em dobro.
Roda na sua máquina, só leitura. Mesmas credenciais do .env de pluggy_amostra.py.

    python3 scripts/pluggy_comparar.py            # usa ./financas.db (ou FINANCAS_DB)

Não imprime descrição, nome nem valor; só quantidades e nomes de campo.
"""
import os
import sqlite3
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pluggy_amostra import chamar, ler_env  # noqa: E402


def todas(chave, conta_id):
    res, proximo = [], None
    for _ in range(50):
        if proximo:
            pg = chamar("/v2/transactions" + (proximo if proximo.startswith("?") else "?" + proximo), chave)
        else:
            pg = chamar("/v2/transactions", chave, params={"accountId": conta_id})
        res += pg.get("results", [])
        proximo = pg.get("next")
        if not proximo:
            break
    return res


def centavos(x) -> int:
    return round(abs(float(x)) * 100)


def casar(local: Counter, remoto: Counter) -> tuple[int, int, int]:
    comuns = sum((local & remoto).values())
    return comuns, sum(local.values()) - comuns, sum(remoto.values()) - comuns


def com_tolerancia(local: Counter, remoto: Counter, dias: int) -> int:
    """Quantos casam se a data puder diferir até 'dias' (consome um a um)."""
    sobra = Counter(remoto)
    n = 0
    for (d, c), q in sorted(local.items()):
        for _ in range(q):
            for delta in sorted(range(-dias, dias + 1), key=abs):
                k = ((date.fromisoformat(d) + timedelta(days=delta)).isoformat(), c)
                if sobra[k] > 0:
                    sobra[k] -= 1
                    n += 1
                    break
    return n


def main() -> None:
    env = ler_env()
    chave = chamar("/auth", corpo={"clientId": env["PLUGGY_CLIENT_ID"], "clientSecret": env["PLUGGY_CLIENT_SECRET"]})["apiKey"]
    contas = chamar("/accounts", chave, params={"itemId": env["PLUGGY_ITEM_ID"]}).get("results", [])
    banco = sqlite3.connect(os.environ.get("FINANCAS_DB", "financas.db"))

    for c in contas:
        tipo = c.get("type")
        txs = [t for t in todas(chave, c["id"]) if t.get("status") == "POSTED"]
        conta = tipo == "BANK"
        conta_local = "nubank_conta" if conta else "nubank_fatura"
        locais = banco.execute("SELECT date, amount_cents FROM transactions WHERE account=?", (conta_local,)).fetchall()
        print(f"\n== {tipo}: Pluggy POSTED={len(txs)}  local({conta_local})={len(locais)}")
        if not locais or not txs:
            continue
        loc = Counter((d, abs(c_)) for d, c_ in locais)
        ini = max(min(d for d, _ in loc), min(str(t["date"])[:10] for t in txs))
        fim = min(max(d for d, _ in loc), max(str(t["date"])[:10] for t in txs))
        print(f"   janela comum: {ini} a {fim}")
        loc = Counter({k: v for k, v in loc.items() if ini <= k[0] <= fim})

        candidatos = {"date": lambda t: str(t["date"])[:10]}
        if not conta:
            candidatos["purchaseDate"] = lambda t: str((t.get("creditCardMetadata") or {}).get("purchaseDate") or t["date"])[:10]
            candidatos["billPostDate"] = lambda t: str((t.get("creditCardMetadata") or {}).get("billPostDate") or t["date"])[:10]
        for nome, f in candidatos.items():
            rem = Counter((f(t), centavos(t["amount"])) for t in txs if ini <= f(t) <= fim)
            ok, so_local, so_remoto = casar(loc, rem)
            print(f"   data={nome:13} casam={ok}  só_local={so_local}  só_pluggy={so_remoto}"
                  f"  | com ±1 dia: {com_tolerancia(loc, rem, 1)}  ±3 dias: {com_tolerancia(loc, rem, 3)}")
        # tipos dos que sobram só no Pluggy (para entender o que o CSV não tem)
        f = candidatos["date"]
        rem = Counter((f(t), centavos(t["amount"])) for t in txs if ini <= f(t) <= fim)
        so_pluggy = rem - loc
        ops = Counter(str(t.get("operationType")) for t in txs
                      if so_pluggy.get((f(t), centavos(t["amount"])), 0) > 0 and ini <= f(t) <= fim)
        print("   só no Pluggy, por operationType:", dict(ops))


if __name__ == "__main__":
    main()
