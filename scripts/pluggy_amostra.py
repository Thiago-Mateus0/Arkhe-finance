"""Mostra a ESTRUTURA dos dados do Meu Pluggy (campos, tipos, contagens), sem nenhum valor pessoal.

Serve para escrever o importador sem que dado real passe pelo chat ou pelo git.
Roda na sua máquina, só leitura. Credenciais vêm do arquivo .env (ignorado pelo git):

    PLUGGY_CLIENT_ID=...
    PLUGGY_CLIENT_SECRET=...
    PLUGGY_ITEM_ID=...        # id da conexão do Nubank

    python scripts/pluggy_amostra.py

Não imprime descrição, nome, valor nem credencial. Só stdlib (sem dependência nova).
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

BASE = "https://api.pluggy.ai"


def ler_env() -> dict:
    env = dict(os.environ)
    arq = Path(__file__).resolve().parent.parent / ".env"
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            if "=" in linha and not linha.lstrip().startswith("#"):
                k, v = linha.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


def chamar(caminho: str, chave: str | None = None, corpo: dict | None = None, params: dict | None = None):
    url = BASE + caminho + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, method="POST" if corpo is not None else "GET")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    if chave:
        req.add_header("X-API-KEY", chave)
    dados = json.dumps(corpo).encode() if corpo is not None else None
    try:
        with urllib.request.urlopen(req, data=dados, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Erro {e.code} em {caminho}. Confira as credenciais e o PLUGGY_ITEM_ID.")


def forma(v, nivel=0):
    """Descreve o tipo, nunca o conteúdo."""
    if isinstance(v, dict):
        return {k: forma(x, nivel + 1) for k, x in v.items()} if nivel < 2 else "objeto"
    if isinstance(v, list):
        return [forma(v[0], nivel + 1)] if v else []
    return type(v).__name__ if v is not None else "null"


def main() -> None:
    env = ler_env()
    faltam = [k for k in ("PLUGGY_CLIENT_ID", "PLUGGY_CLIENT_SECRET", "PLUGGY_ITEM_ID") if not env.get(k)]
    if faltam:
        raise SystemExit(f"Faltam no .env: {', '.join(faltam)}")
    chave = chamar("/auth", corpo={"clientId": env["PLUGGY_CLIENT_ID"], "clientSecret": env["PLUGGY_CLIENT_SECRET"]})["apiKey"]

    item = chamar(f"/items/{env['PLUGGY_ITEM_ID']}", chave)
    print("== conexão")
    for campo in ("status", "executionStatus", "lastUpdatedAt", "createdAt", "updatedAt"):
        if campo in item:
            print(f"  {campo}: {item[campo]}")
    print("  campos:", json.dumps(forma({k: v for k, v in item.items() if k != 'parameter'}), ensure_ascii=False))

    contas = chamar("/accounts", chave, params={"itemId": env["PLUGGY_ITEM_ID"]}).get("results", [])
    print(f"== contas: {len(contas)}")
    for c in contas:
        print(f"-- tipo={c.get('type')} subtipo={c.get('subtype')} moeda={c.get('currencyCode')}")
        print("   campos:", json.dumps(forma(c), ensure_ascii=False))
        pagina = chamar("/transactions", chave, params={"accountId": c["id"], "pageSize": 500})
        res = pagina.get("results", [])
        print(f"   transações na 1ª página: {len(res)}  total={pagina.get('total')} páginas={pagina.get('totalPages')}")
        if not res:
            continue
        print("   campos:", json.dumps(forma(res[0]), ensure_ascii=False))
        datas = sorted(t.get("date", "")[:10] for t in res)
        print(f"   período: {datas[0]} a {datas[-1]}")
        for campo in ("type", "status", "currencyCode"):
            print(f"   {campo}:", dict(Counter(str(t.get(campo)) for t in res)))
        sinal = Counter((str(t.get("type")), "negativo" if (t.get("amount") or 0) < 0 else "positivo") for t in res)
        print("   sinal do valor por tipo:", {f"{a}/{b}": n for (a, b), n in sinal.items()})
        for extra in ("creditCardMetadata", "paymentData", "merchant"):
            print(f"   {extra} presente em:", sum(1 for t in res if t.get(extra)), "de", len(res))
        parcelas = [t["creditCardMetadata"] for t in res if t.get("creditCardMetadata")]
        if parcelas:
            print("   campos de cartão:", json.dumps(forma(parcelas[0]), ensure_ascii=False))
        print("   descrições com 'pix'/'parcela':", sum(1 for t in res if any(p in (t.get("description") or "").lower() for p in ("pix", "parcela"))))


if __name__ == "__main__":
    sys.exit(main())
