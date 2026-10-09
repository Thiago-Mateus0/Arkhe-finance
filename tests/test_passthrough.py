from financas.classifier import EXPENSE, INCOME, PASSTHROUGH, mark_passthrough


def row(i, date, cents, who):
    return {"source_id": str(i), "date": date, "amount_cents": cents, "counterparty": who,
            "kind": INCOME if cents > 0 else EXPENSE}


def kinds(rows):
    return [r["kind"] for r in rows]


def test_exact_same_day_pair():
    rows = [row(1, "2026-09-01", 5000, "AMIGO"), row(2, "2026-09-01", -5000, "APP")]
    mark_passthrough(rows)
    assert kinds(rows) == [PASSTHROUGH, PASSTHROUGH]


def test_sum_of_incomes_across_days_for_known_conduit():
    rows = [
        row(1, "2026-09-01", 2000, "A"), row(2, "2026-09-01", -2000, "APP"),  # ensina que APP é condutor
        row(3, "2026-09-07", 1000, "B"), row(4, "2026-09-08", 1000, "B"),
        row(5, "2026-09-08", -2000, "APP"),  # = 10 + 10, em dias diferentes
    ]
    mark_passthrough(rows)
    assert kinds(rows) == [PASSTHROUGH] * 5


def test_sum_matching_ignores_unknown_counterparty():
    rows = [row(1, "2026-09-07", 1000, "B"), row(2, "2026-09-07", 1000, "B"), row(3, "2026-09-08", -2000, "LOJA")]
    mark_passthrough(rows)
    assert kinds(rows) == [INCOME, INCOME, EXPENSE]  # gasto de verdade continua gasto


def test_sum_matching_respects_window_and_exactness():
    rows = [
        row(1, "2026-09-01", 2000, "A"), row(2, "2026-09-01", -2000, "APP"),
        row(3, "2026-09-02", 1000, "B"), row(4, "2026-09-20", -1000, "APP"),  # fora da janela
        row(5, "2026-09-02", 700, "C"), row(6, "2026-09-03", -1100, "APP"),  # soma não bate
    ]
    mark_passthrough(rows)
    assert [r["kind"] for r in rows[2:]] == [INCOME, EXPENSE, INCOME, EXPENSE]


def test_prefers_recent_combination_over_old_single_income():
    rows = [
        row(1, "2026-09-01", 2000, "A"), row(2, "2026-09-01", -2000, "APP"),  # APP é condutor
        row(3, "2026-09-03", 3000, "FAMILIA"),  # entrada real, antiga e avulsa
        row(4, "2026-09-05", 1000, "B"), row(5, "2026-09-05", 2000, "C"),
        row(6, "2026-09-05", -3000, "APP"),
    ]
    mark_passthrough(rows)
    assert rows[2]["kind"] == INCOME
    assert [r["kind"] for r in rows[3:]] == [PASSTHROUGH] * 3
