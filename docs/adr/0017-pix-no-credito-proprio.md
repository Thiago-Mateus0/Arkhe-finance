# ADR 0017 — Pix no crédito para o próprio dono é transferência

- **Status:** Aceito
- **Data:** 2026-10-10
- **Fase:** 3 — Uso real
- **Decidido por:** Thiago ("transferência")

## Contexto

O ADR 0004 definiu os tipos de lançamento e deixou em aberto o Pix no crédito (P3). Na fatura ele aparece como "Pix no Crédito - NOME". No uso real, o Thiago tem Pix no crédito para uma conta dele mesmo, e esse lançamento entrava como **gasto**, inflando o total, embora o dinheiro só tenha mudado de bolso.

## Decisão

Linha de fatura "Pix no Crédito - NOME" (com ou sem sufixo de parcela, "- 2/3") cujo NOME é um **nome próprio** vira `transfer` e não conta como gasto. Com NOME de terceiro, nada muda: segue `gasto`.

## Consequências

- Complementa o ADR 0004; não o revoga.
- A classificação da fatura passa a depender de `own_names` e é recalculada a cada importação e a cada mudança de nome próprio (antes era fixa na importação).
- O Pix no crédito para **terceiro** ainda pode contar duas vezes (fatura e conta). Fica em P3.
