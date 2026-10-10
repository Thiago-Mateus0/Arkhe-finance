# ADR 0018 — Pix no crédito para terceiro conta uma vez, pela fatura

- **Status:** Aceito
- **Data:** 2026-10-10
- **Fase:** 3 — Uso real
- **Decidido por:** Thiago ("conta uma vez, fica como fatura de crédito")

## Contexto

Um Pix feito no crédito deixa rastro em dois lugares: na conta (entrada fictícia mais o Pix de saída, com o mesmo identificador) e na fatura ("Pix no Crédito - NOME"). O ADR 0004 registrou o risco de contar duas vezes. A fatura traz um valor **maior** que o Pix, porque inclui o custo do crédito, então os dois lados não têm o mesmo valor.

## Decisão

Conta **uma vez, pela fatura**: ela mostra o que o crédito realmente custou. A saída da conta deixa de contar (vira `credit_funding`) quando existe a linha da fatura correspondente. O pareamento é por nome, um para um, em janela de datas (ver `docs/spec/classificacao.md`, regra 7). Sem a linha da fatura, a saída continua gasto, para que o dinheiro não suma dos totais.

## Consequências

- Complementa os ADRs 0004 e 0017; não revoga nenhum.
- Importar a fatura depois reclassifica a conta: o gasto "muda de lugar" da conta para a fatura, no mês da fatura.
- O pareamento por nome e data pode errar entre duas saídas parecidas para a mesma pessoa; por isso é um para um e prefere a saída compatível em valor.
