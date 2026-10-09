# ADR 0002 — CSV primeiro, Open Finance depois

- **Status:** Aceito
- **Data:** 2026-10-06
- **Fase:** 1 — Fundação
- **Decidido por:** Thiago

## Contexto

Há dois caminhos para ter os lançamentos: importar o CSV que o banco exporta, ou conectar via Open Finance por um agregador (que tem custo, credenciais e burocracia). O dono usa o Nubank e consegue exportar conta e fatura.

## Decisão

A versão 1 importa **CSV** (conta e fatura do Nubank). O Open Finance entra em fase posterior, **atrás da mesma camada de importação**: o que muda é a origem dos lançamentos, não a classificação nem os relatórios.

## Consequências

- Dá para usar o app já, sem conta em agregador.
- Cada banco novo exige um parser novo (os formatos diferem). Fica registrado em `docs/pendencias.md`.
- O custo real de manter só aparece com Open Finance (ver pendências).
