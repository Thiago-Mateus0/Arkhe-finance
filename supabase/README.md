# Supabase (ADR 0025)

`migrations/` guarda o esquema do Postgres hospedado, em SQL puro. Cada arquivo roda uma vez, em ordem.

## Aplicar no seu projeto (feito pelo Thiago)

1. No painel do Supabase, abra **SQL Editor** → **New query**.
2. Cole o conteúdo de `migrations/20261014000001_esquema_e_rls.sql` e clique em **Run**.
3. Em **Table Editor**, confira que aparecem `households`, `members`, `transactions`, `rules`, `budgets`, `own_names` e `meta`, cada uma com o selo **RLS enabled**.

Nenhuma chave, URL ou dado real vai para este repositório.

## Testes

`tests/test_supabase_rls.py` sobe um Postgres 16 descartável no Docker e prova o isolamento (A nunca lê, grava ou apaga dado de B). Pula sozinho se não houver Docker com a imagem `postgres:16`. Os dados são fictícios.
