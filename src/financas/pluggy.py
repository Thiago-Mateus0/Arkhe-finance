"""Importador do Meu Pluggy (ADRs 0020 e 0022): lê conta e cartão pela API v2 e grava pelo mesmo
caminho do CSV, sem contar em dobro o que já veio por arquivo.

Credenciais ficam só na máquina do dono: variáveis de ambiente ou o arquivo .env (ignorado pelo git).
Tudo que vem da API é não confiável: valida antes de gravar e ignora a linha que não fecha.
"""
import hashlib
import json
import math
import os
import re
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from decimal import Decimal
from pathlib import Path

from . import service
from .importer import ParsedRow, counterparty_of

BASE = "https://api.pluggy.ai"
MAX_PAGINAS = 100
CONTA, FATURA = "nubank_conta", "nubank_fatura"
_PARCELA_NO_FIM = re.compile(r"\b\d+/\d+\s*$")


class ErroPluggy(RuntimeError):
    pass


# ---------- leitura da API ----------

def _ler_env() -> dict:
    env = dict(os.environ)
    arq = Path(".env")
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            if "=" in linha and not linha.lstrip().startswith("#"):
                k, v = linha.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


class PluggyAPI:
    """Cliente mínimo (só leitura). Rota nova de transações: GET /v2/transactions, cursor em 'next'."""

    def __init__(self, env: dict | None = None):
        env = env if env is not None else _ler_env()
        faltam = [k for k in ("PLUGGY_CLIENT_ID", "PLUGGY_CLIENT_SECRET", "PLUGGY_ITEM_ID") if not env.get(k)]
        if faltam:
            raise ErroPluggy(f"Faltam no .env ou no ambiente: {', '.join(faltam)}")
        self._env, self._chave = env, None

    def _chamar(self, caminho: str, params: dict | None = None, corpo: dict | None = None):
        url = BASE + caminho + ("?" + urllib.parse.urlencode(params) if params else "")
        req = urllib.request.Request(url, method="POST" if corpo is not None else "GET")
        req.add_header("Content-Type", "application/json")
        if self._chave:
            req.add_header("X-API-KEY", self._chave)
        try:
            with urllib.request.urlopen(req, data=json.dumps(corpo).encode() if corpo is not None else None, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            raise ErroPluggy(f"Pluggy respondeu {e.code} em {caminho}") from None
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            raise ErroPluggy(f"Falha ao falar com o Pluggy: {type(e).__name__}") from None

    def _autenticar(self) -> None:
        if not self._chave:
            r = self._chamar("/auth", corpo={"clientId": self._env["PLUGGY_CLIENT_ID"],
                                             "clientSecret": self._env["PLUGGY_CLIENT_SECRET"]})
            self._chave = r.get("apiKey")
            if not self._chave:
                raise ErroPluggy("Pluggy não devolveu a chave de acesso")

    def contas(self) -> list[dict]:
        self._autenticar()
        return self._chamar("/accounts", {"itemId": self._env["PLUGGY_ITEM_ID"]}).get("results", [])

    def transacoes(self, conta_id: str) -> list[dict]:
        self._autenticar()
        res, proximo = [], None
        for _ in range(MAX_PAGINAS):
            if proximo:  # 'next' é uma query string pronta; anexa como está
                pg = self._chamar("/v2/transactions" + (proximo if proximo.startswith("?") else "?" + proximo))
            else:
                pg = self._chamar("/v2/transactions", {"accountId": conta_id})
            res += pg.get("results", [])
            proximo = pg.get("next")
            if not proximo:
                return res
        raise ErroPluggy("Mais páginas do que o esperado; parei por segurança")


# ---------- tradução para o formato interno ----------

def _centavos(amount) -> int | None:
    if isinstance(amount, bool) or not isinstance(amount, (int, float, Decimal)):
        return None
    if isinstance(amount, float) and not math.isfinite(amount):
        return None
    d = Decimal(str(amount))
    return int((abs(d) * 100).to_integral_value()) if d.is_finite() else None


def _data(valor) -> str | None:
    if not isinstance(valor, str) or len(valor) < 10:
        return None
    try:
        return date.fromisoformat(valor[:10]).isoformat()
    except ValueError:
        return None


def _inteiro(valor) -> int | None:
    return valor if isinstance(valor, int) and not isinstance(valor, bool) else None


def traduzir(conta: str, t: dict) -> ParsedRow | None:
    """Uma transação do Pluggy -> linha interna. None se não for gravável (pendente, malformada).
    Direção SEMPRE pelo 'type': no cartão o sinal do 'amount' vem invertido (compra positiva)."""
    if not isinstance(t, dict) or t.get("status") != "POSTED":
        return None
    tipo, centavos, id_ = t.get("type"), _centavos(t.get("amount")), t.get("id")
    cc = t.get("creditCardMetadata") if isinstance(t.get("creditCardMetadata"), dict) else {}
    # cartão: a data do CSV é a do lançamento na fatura (ADR 0022); na conta, a própria data
    data = (_data(cc.get("billPostDate")) if conta == FATURA else None) or _data(t.get("date"))
    desc = t.get("descriptionRaw") or t.get("description")
    if tipo not in ("DEBIT", "CREDIT") or centavos is None or data is None or not isinstance(id_, str) \
            or not id_ or not isinstance(desc, str) or not desc.strip():
        return None
    desc = " ".join(desc.split())
    n, total = _inteiro(cc.get("installmentNumber")), _inteiro(cc.get("totalInstallments"))
    if conta == FATURA and n and total and total > 1 and not _PARCELA_NO_FIM.search(desc):
        desc = f"{desc} - Parcela {n}/{total}"  # mesmo formato do CSV, que o resto do app já entende
    op = t.get("operationType") if isinstance(t.get("operationType"), str) else ""
    return ParsedRow(
        date=data, amount_cents=-centavos if tipo == "DEBIT" else centavos, source_id=id_, description=desc,
        counterparty=desc.upper() if conta == FATURA else counterparty_of(desc),
        dedupe_key=hashlib.sha256(f"pluggy|{id_}".encode()).hexdigest(), external_id=id_, operation_type=op,
    )


def sincronizar(conn: sqlite3.Connection, api=None) -> dict:
    api = api or PluggyAPI()
    service.seed_default_rules_once(conn)
    tot = {"lidas": 0, "novas": 0, "duplicadas": 0, "ignoradas": 0, "pendentes": 0}
    for c in api.contas():
        conta = {"BANK": CONTA, "CREDIT": FATURA}.get(c.get("type"))
        if conta is None:
            continue
        linhas = []
        for t in api.transacoes(c["id"]):
            if isinstance(t, dict) and t.get("status") == "PENDING":
                tot["pendentes"] += 1
                continue
            p = traduzir(conta, t)
            if p is None:
                tot["ignoradas"] += 1
            else:
                linhas.append(p)
        novas = service.gravar_linhas(conn, conta, linhas, "pluggy")
        tot["lidas"] += len(linhas)
        tot["novas"] += novas
        tot["duplicadas"] += len(linhas) - novas
    service.reclassify(conn)
    return tot
