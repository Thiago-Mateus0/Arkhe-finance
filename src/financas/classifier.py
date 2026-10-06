"""Define o tipo de cada transação. Só 'expense' entra no total de gastos."""

EXPENSE = "expense"
INCOME = "income"
TRANSFER = "transfer"  # entre contas próprias
CARD_PAYMENT = "card_payment"  # pagamento de fatura (os gastos reais estão na fatura)
CREDIT_FUNDING = "credit_funding"  # Pix no crédito: entrada fictícia, o gasto é o Pix de saída
PASSTHROUGH = "passthrough"  # recebeu e repassou o mesmo valor no mesmo dia

EXCLUDED_FROM_SPENDING = {TRANSFER, CARD_PAYMENT, CREDIT_FUNDING, PASSTHROUGH, INCOME}


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
