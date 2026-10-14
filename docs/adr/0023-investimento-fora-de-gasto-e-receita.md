# ADR 0023 — Aplicação e resgate de investimento não são gasto nem receita

- **Status:** Aceito
- **Data:** 2026-10-14
- **Fase:** 6a — Fonte automática
- **Decidido por:** Thiago ("sim")

## Contexto

Nos dados reais, "Aplicação RDB" entrava como **gasto** e "Resgate RDB" como **receita**, inflando os dois totais. Guardar dinheiro num investimento ou resgatá-lo não é gastar nem receber: o dinheiro só muda de lugar. O Meu Pluggy traz o histórico inteiro, e o erro cresceria nos meses antigos (pendência P18).

## Decisão

Existe um tipo novo, `investment` (investimento). Entra nele a linha cuja descrição **começa** com "Aplicação" ou "Resgate", ou cuja operação no Pluggy é `RESGATE_APLIC_FINANCEIRA`. Não conta como gasto nem como receita, igual à transferência, e aparece no filtro **Não contam**.

## Consequências

- Complementa o ADR 0004 (tipos de lançamento); não o revoga.
- Só o início da descrição vale: "Aplicativo" e nomes com "resgate" no meio (Pix para uma empresa, por exemplo) continuam gasto.
- Aplicação e resgate do mesmo valor no mesmo dia deixam de virar repasse; seguem investimento.
- Rendimento de aplicação (se vier como lançamento separado) ainda não está tratado.
- Meses já importados mudam de total ao reclassificar: o gasto cai pelo que foi aplicado e a receita cai pelo que foi resgatado.
