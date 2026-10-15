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

## Levar o seu banco local para a nuvem (etapa 5)

Leva lançamentos, regras, nomes próprios, orçamentos e categorias travadas do SQLite local para a nuvem, **sem reclassificar**. Só lê o banco local e confere os totais (por conta, tipo e categoria) antes de gravar; se não baterem, nada é gravado. Rodar de novo não duplica.

1. Teste antes, sem gravar nada: `.venv/bin/python -m financas nuvem migrar --simular`
2. Se mostrar "conferido", rode de verdade: `.venv/bin/python -m financas nuvem migrar`

Seus dados reais passam a existir no Supabase depois do passo 2 (decisão do ADR 0025). O banco local não é alterado.

## Relatórios em SQL (etapa 3)

A migração `20261014000002_relatorios.sql` cria as funções `meses_com_dados`, `relatorio_mensal`, `relatorio_diario`, `orcamento_status`, `assinaturas_do_mes` e `parcelas_a_vir`, com o mesmo formato JSON da API local. Cada pessoa logada vê só a sua casa. Aplique como a primeira: **SQL Editor → New query → cole o conteúdo do arquivo → Run**.

## Testes

`tests/test_supabase_rls.py` sobe um Postgres 16 descartável no Docker e prova o isolamento (A nunca lê, grava ou apaga dado de B). `tests/test_nuvem_paridade.py` prova que o importador dá o mesmo resultado no Postgres e no SQLite. `tests/test_nuvem_relatorios.py` prova que cada relatório em SQL dá o mesmo resultado que o Python. Pula sozinho se não houver Docker com a imagem `postgres:16`. Os dados são fictícios.
