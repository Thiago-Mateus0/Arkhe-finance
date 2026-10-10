# ADR 0011 — Dinheiro em centavos inteiros

- **Status:** Aceito
- **Data:** 2026-10-06
- **Fase:** 1 — Fundação
- **Decidido por:** Claude, por delegação do Thiago ("tome as melhores decisões"); **aguarda revisão do Thiago**

## Contexto

Somar `float` acumula erro de centavo, e o produto é justamente somar dinheiro.

## Decisão

O banco guarda `amount_cents` (inteiro). O parser converte com `Decimal` (nunca `float`). A API devolve reais, só na borda. Saída é negativa, entrada é positiva.

## Consequências

- Totais exatos. Os testes comparam valores em reais já convertidos; ao testar soma, prefira centavos.
- Quem escrever código novo deve respeitar a fronteira: dentro, centavos; fora, reais.
