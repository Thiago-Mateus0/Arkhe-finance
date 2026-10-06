"""Define o tipo de cada transação. Só 'expense' entra no total de gastos."""
from datetime import date
from itertools import combinations

EXPENSE = "expense"
INCOME = "income"
TRANSFER = "transfer"  # entre contas próprias
CARD_PAYMENT = "card_payment"  # pagamento de fatura (os gastos reais estão na fatura)
CREDIT_FUNDING = "credit_funding"  # Pix no crédito: entrada fictícia, o gasto é o Pix de saída
PASSTHROUGH = "passthrough"  # recebeu e repassou o mesmo valor no mesmo dia

EXCLUDED_FROM_SPENDING = {TRANSFER, CARD_PAYMENT, CREDIT_FUNDING, PASSTHROUGH, INCOME}


def classify_fatura(description: str, amount_cents: int) -> str:
    if description.lower().startswith("pagamento recebido"):
        return CARD_PAYMENT
    return EXPENSE  # inclui estornos (valor positivo = reduz o gasto)


def classify(description: str, amount_cents: int, counterparty: str, own_names: set[str]) -> str:
    d = description.lower()
    if d.startswith("pagamento de fatura"):
        return CARD_PAYMENT
    if d.startswith("valor adicionado na conta por cartão de crédito"):
        return CREDIT_FUNDING
    if counterparty and counterparty in own_names:
        return TRANSFER
    return INCOME if amount_cents > 0 else EXPENSE


def mark_passthrough(rows: list[dict]) -> None:
    """Pareia entrada e saída de mesmo valor no mesmo dia (dinheiro de passagem).

    Cada entrada consome no máximo uma saída; sobras continuam como income/expense.
    Altera 'kind' in-place nas linhas income/expense.
    """
    pending: dict[tuple[str, int], list[dict]] = {}
    for r in sorted(rows, key=lambda r: (r["date"], r["source_id"])):
        if r["kind"] not in (INCOME, EXPENSE):
            continue
        key = (r["date"], abs(r["amount_cents"]))
        opposite = [p for p in pending.get(key, []) if (p["amount_cents"] > 0) != (r["amount_cents"] > 0)]
        if opposite:
            other = opposite[0]
            pending[key].remove(other)
            other["kind"] = r["kind"] = PASSTHROUGH
        else:
            pending.setdefault(key, []).append(r)
    _match_conduit_sums(rows)


def _match_conduit_sums(rows: list[dict], window_days: int = 3, max_parts: int = 4) -> None:
    """Segunda fase: saída = soma de várias entradas (até 'window_days' antes).

    Só vale para contrapartes "condutoras": aquelas cuja saída já foi pareada exatamente na
    primeira fase (ex.: um app que repassa Pix de amigos). Evita esconder gastos de verdade."""
    conduits = {r["counterparty"] for r in rows
                if r["kind"] == PASSTHROUGH and r["amount_cents"] < 0 and r.get("counterparty")}
    outs = sorted((r for r in rows if r["kind"] == EXPENSE and r.get("counterparty") in conduits),
                  key=lambda r: (r["date"], r["source_id"]))
    for out in outs:
        d_out = date.fromisoformat(out["date"])
        cands = [r for r in rows if r["kind"] == INCOME
                 and 0 <= (d_out - date.fromisoformat(r["date"])).days <= window_days]
        cands.sort(key=lambda r: r["date"], reverse=True)  # mais próximas primeiro
        cands = cands[:12]
        target = -out["amount_cents"]
        # Entre as combinações que fecham a soma, vale a mais recente (menor distância até a saída);
        # em empate, a de menos partes. Assim uma entrada antiga e avulsa não é "consumida" à toa.
        hits = [c for size in range(1, max_parts + 1) for c in combinations(cands, size)
                if sum(x["amount_cents"] for x in c) == target]
        if hits:
            best = max(hits, key=lambda c: (min(x["date"] for x in c), -len(c)))
            out["kind"] = PASSTHROUGH
            for x in best:
                x["kind"] = PASSTHROUGH
