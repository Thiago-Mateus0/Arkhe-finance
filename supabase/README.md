# Supabase (ADR 0025)

`migrations/` guarda o esquema do Postgres hospedado, em SQL puro. Cada arquivo roda uma vez, em ordem.

## Aplicar no seu projeto (feito pelo Thiago)

1. No painel do Supabase, abra **SQL Editor** → **New query**.
2. Cole o conteúdo de `migrations/20261014000001_esquema_e_rls.sql` e clique em **Run**.
3. Em **Table Editor**, confira que aparecem `households`, `members`, `transactions`, `rules`, `budgets`, `own_names` e `meta`, cada uma com o selo **RLS enabled**.

Nenhuma chave, URL ou dado real vai para este repositório.

## Gravar no Supabase com o importador (etapa 2)

Só depois da migração aplicada. Isto é feito por você, no seu computador; a chave nunca vai para o chat.

1. No **SQL Editor**, rode: `insert into households (name) values ('Thiago') returning id;` e copie o `id` que aparecer.
2. No `.env` da pasta do projeto (ignorado pelo git), preencha `ARKHE_HOUSEHOLD_ID` com esse id e `SUPABASE_DB_URL` com a *Connection string* (URI) de **Project Settings → Database**.
3. Instale o driver uma vez: `.venv/bin/pip install -e ".[nuvem]"`.
4. Importe: `.venv/bin/python -m financas nuvem import samples/extrato.csv samples/fatura.csv`. Reimportar não muda nada.

O app local (SQLite) continua como está; a virada para a nuvem é a etapa 5.

## Testes

`tests/test_supabase_rls.py` sobe um Postgres 16 descartável no Docker e prova o isolamento (A nunca lê, grava ou apaga dado de B). `tests/test_nuvem_paridade.py` prova que o importador dá o mesmo resultado no Postgres e no SQLite. Pula sozinho se não houver Docker com a imagem `postgres:16`. Os dados são fictícios.
