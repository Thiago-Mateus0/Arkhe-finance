# ADR 0006 — Categorias por regras, categoria manual trava

- **Status:** Aceito
- **Data:** 2026-10-06
- **Fase:** 1 — Fundação
- **Decidido por:** Thiago

## Contexto

Era preciso categorizar sem custo e de forma previsível. A alternativa de usar IA para sugerir categorias enviaria as descrições dos lançamentos a uma API externa. Sobre os Pix para pessoas, o nome não diz o motivo do gasto.

## Decisão

**Regras que o dono define** (trecho de texto → categoria; maior prioridade vence, empate vai para o padrão mais longo). O que nenhuma regra resolve fica **pendente** e o dono categoriza **à mão**; a escolha manual trava a transação e, se o dono quiser, cria uma regra ("lembrar").

## Consequências

- Previsível, sem custo e sem enviar dados a terceiros.
- Há um conjunto de regras padrão (`default_rules.json`), carregado uma vez; é ponto de partida, não verdade.
- Pix para pessoas continuam pendentes até o dono marcar a primeira vez.
