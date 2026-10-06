"""Regras de categoria: o padrão (substring, sem caixa) da maior prioridade vence;
empate vai para o padrão mais longo (mais específico)."""
UNCATEGORIZED = "Sem categoria"


def pick_category(description: str, counterparty: str, rules: list[dict]) -> str:
    text = f"{description} {counterparty}".lower()
    hits = [r for r in rules if r["pattern"].lower() in text]
    if not hits:
        return UNCATEGORIZED
    best = max(hits, key=lambda r: (r["priority"], len(r["pattern"])))
    return best["category"]
