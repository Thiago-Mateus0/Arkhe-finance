# ADR 0012 — Parcelas futuras: projetar

- **Status:** Aceito — ainda não implementado
- **Data:** 2026-10-06
- **Fase:** 4 — Controle
- **Decidido por:** Thiago

## Contexto

Compras parceladas no cartão comprometem meses futuros. A alternativa seria mostrar só o que já está na fatura, sem enxergar o comprometido.

## Decisão

Detectar "n/m" na descrição da fatura e **projetar as parcelas restantes** como compromissos futuros.

## Consequências

- Bloqueado: ainda não há CSV de fatura com compra parcelada para descobrir como o Nubank escreve isso. Ver `docs/pendencias.md`.
- Quando existir, é uma nova leitura sobre a mesma tabela, sem mudar a importação.
