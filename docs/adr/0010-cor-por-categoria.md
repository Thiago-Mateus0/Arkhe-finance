# ADR 0010 — Cor por categoria, paleta validada

- **Status:** Aceito
- **Data:** 2026-10-09
- **Fase:** 2 — Interface
- **Decidido por:** Claude, por delegação do Thiago ("tome as melhores decisões"); **aguarda revisão do Thiago**

## Contexto

Gráficos de categoria precisam ser legíveis para quem tem daltonismo e a cor não pode mudar de dono quando o ranking muda (a cor de "Transporte" não pode virar a de "Saúde" porque o mês foi diferente).

## Decisão

Cada categoria conhecida tem **uma cor fixa**, tirada de uma paleta categórica de 8 posições validada com o validador da skill `dataviz` (contraste, separação para daltonismo, faixa de luminosidade) sobre a cor do cartão (`#1a1a19`). Categorias sem cor própria ficam em cinza e, na rosca, são agrupadas em "Outras categorias". A lista de categorias é a legenda; o sinal (+/−) acompanha a cor dos valores.

## Consequências

- A paleta passou em todas as verificações; a separação para daltonismo fica perto do mínimo recomendado, por isso as fatias da rosca têm folga e a lista as nomeia.
- Só 8 categorias têm cor. Uma categoria nova do usuário aparece em cinza até haver decisão de como atribuir cores a categorias livres (`docs/pendencias.md`).
- Tema claro: ver ADR 0014.
