# ADR 0008 — household_id desde o início

- **Status:** Aceito
- **Data:** 2026-10-06
- **Fase:** 1 — Fundação
- **Decidido por:** Thiago

## Contexto

Uso é só do dono agora, mas ele pode compartilhar com mais uma pessoa depois. Acrescentar a noção de "casa" em um banco já cheio de dados é uma migração dolorosa.

## Decisão

Toda tabela de dados tem `household_id` (hoje sempre `default`) e as consultas já filtram por ele. Não há login: autenticação só entra quando houver compartilhamento (fase 6).

## Consequências

- Compartilhar vira migração de infraestrutura e login, não reescrita do modelo.
- Hoje o campo não protege nada; é só preparação. A API não tem autenticação e **não deve ser exposta na internet** como está.
