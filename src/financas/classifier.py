"""Define o tipo de cada transação. Só 'expense' entra no total de gastos."""
import re
from datetime import date
from itertools import combinations

EXPENSE = "expense"
INCOME = "income"
TRANSFER = "transfer"  # entre contas próprias
CARD_PAYMENT = "card_payment"  # pagamento de fatura (os gastos reais estão na fatura)
CREDIT_FUNDING = "credit_funding"  # Pix no crédito: entrada fictícia, o gasto é o Pix de saída
PASSTHROUGH = "passthrough"  # recebeu e repassou o mesmo valor no mesmo dia

EXCLUDED_FROM_SPENDING = {TRANSFER, CARD_PAYMENT, CREDIT_FUNDING, PASSTHROUGH, INCOME}


_PIX_NO_CREDITO = re.compile(r"^pix no crédito - (?P<nome>.+?)(?: - \d+/\d+)?$", re.IGNORECASE)


def _nome_pix_no_credito(description: str) -> str | None:
    m = _PIX_NO_CREDITO.match(" ".join(description.split()))
    return " ".join(m.group("nome").split()).upper() if m else None


def _pix_no_credito_para(description: str, own_names: set[str]) -> bool:
    """Pix no crédito (com ou sem parcela) cujo destino é uma conta do próprio dono."""
    return _nome_pix_no_credito(description) in own_names


def classify_fatura(description: str, amount_cents: int, own_names: set[str] = frozenset()) -> str:
    if description.lower().startswith("pagamento recebido"):
        return CARD_PAYMENT
    if _pix_no_credito_para(description, own_names):
        return TRANSFER  # o dinheiro só mudou de bolso; o gasto real é quando ele for usado
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


JANELA_PIX_NO_CREDITO_DIAS = 45


def pair_pix_no_credito(conta: list[dict], fatura: list[dict]) -> None:
    """Pix no crédito para terceiro conta uma vez: fica a linha da fatura, a saída da conta deixa de contar.

    A saída da conta é a que tem uma entrada fictícia (CREDIT_FUNDING) com o mesmo identificador e valor
    oposto. A fatura traz "Pix no Crédito - NOME" com valor MAIOR (custo do crédito), então o pareamento
    é por nome, um para um, com a saída até JANELA dias antes da linha (a mais próxima primeiro).
    Sem linha na fatura (ainda não importada) a saída continua gasto. Altera 'kind' in-place.
    """
    financiados = {(r["source_id"], -r["amount_cents"]) for r in conta if r["kind"] == CREDIT_FUNDING}
    saidas = [r for r in conta if r["kind"] == EXPENSE and r["amount_cents"] < 0
              and (r["source_id"], r["amount_cents"]) in financiados]
    linhas = sorted((f for f in fatura if f["kind"] == EXPENSE and _nome_pix_no_credito(f["description"])),
                    key=lambda f: f["date"])
    for f in linhas:
        nome, d_f = _nome_pix_no_credito(f["description"]), date.fromisoformat(f["date"])
        cands = [r for r in saidas if r["kind"] == EXPENSE and r.get("counterparty") == nome
                 and 0 <= (d_f - date.fromisoformat(r["date"])).days <= JANELA_PIX_NO_CREDITO_DIAS]
        # A linha da fatura só soma custo ao Pix: saída maior que ela não é a dela (salvo parcelado,
        # em que cada linha é uma fração; aí vale só a proximidade de data).
        compat = [r for r in cands if -r["amount_cents"] <= -f["amount_cents"]]
        if cands:
            max(compat or cands, key=lambda r: r["date"])["kind"] = CREDIT_FUNDING


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
