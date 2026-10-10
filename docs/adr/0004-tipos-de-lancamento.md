# ADR 0004 — O que não conta como gasto

- **Status:** Aceito
- **Data:** 2026-10-06
- **Fase:** 1 — Fundação
- **Decidido por:** Claude, por delegação do Thiago ("tome as melhores decisões"); **aguarda revisão do Thiago**

## Contexto

Somar tudo que sai da conta dá um número errado: pagamento de fatura repete os gastos que já estão na fatura; transferência entre contas do próprio dono não é gasto; o Pix no crédito cria uma entrada que nunca foi dinheiro novo. Contar tudo inflaria gastos e receitas.

## Decisão

Cada lançamento recebe um **tipo** (gasto, receita, transferência, pagamento de fatura, Pix no crédito, repasse — ver `docs/spec/classificacao.md`). Só gasto e receita entram nos totais. A conta do dono é identificada por **nome** (`FINANCAS_OWN_NAMES`), porque o CSV não diz de quem é a conta de destino.

## Consequências

- Os totais batem com a realidade do dono.
- O Pix no crédito conta uma vez: o Pix de saída é gasto, a entrada fictícia não. Risco aberto: se o mesmo Pix também aparecer na fatura, pode contar duas vezes (`docs/pendencias.md`).
- Cada tipo tem teste. Quem não é reconhecido como "seu" por nome vira gasto.
