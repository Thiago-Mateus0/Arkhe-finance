# ADR 0025 — Supabase como backend hospedado (Postgres, Auth e RLS)

- **Status:** Aceito em 2026-10-14 (a decisão de usar Supabase); as etapas abaixo são um plano e cada uma vira PR
- **Data:** 2026-10-14
- **Fase:** 6 — Automático e compartilhado
- **Decidido por:** Thiago: "quero algo igual o Lifetrailer, deployado" e, depois de ver a alternativa do contêiner com o código atual, "prefiro o Supabase agora". Claude havia recomendado o contêiner pelo custo de reescrita; o Thiago assumiu esse custo
- **Revoga em parte:** [ADR 0001](0001-stack.md) (backend FastAPI + SQLite local). Mantém Python no importador (ver Decisão)
- **Substitui:** [ADR 0024](0024-hospedagem-com-login.md) (hospedagem com login). Os requisitos de segurança do 0024 continuam valendo
- **Mantém:** [ADR 0011](0011-centavos-inteiros.md) (centavo inteiro; em Postgres, `bigint`) e [ADR 0008](0008-household-id.md) (`household_id`)

## Contexto

O Thiago quer o Arkhe no ar, aberto no celular de qualquer lugar, sem depender do computador ligado, como o Lifetrailer. Ele respondeu **casas separadas** (P20): a outra pessoa vê só o que é dela. Hospedar põe dado financeiro real num serviço de terceiro (P21), que ele aceita ao escolher esta rota.

O Lifetrailer já usa Supabase (Postgres + Auth + RLS) e Cloudflare Pages (ADR 0011 do projeto dele). Isso dá ao Thiago uma stack que ele conhece e um isolamento por usuário feito **no banco**, mais difícil de errar do que um filtro na aplicação.

## Decisão

| Camada | Escolha |
|---|---|
| Banco | Postgres no Supabase; dinheiro em `bigint` (centavos) |
| Login | Supabase Auth; cada usuário pertence a um `household_id` |
| Isolamento | RLS em toda tabela, por `household_id`; **sem** `service_role` no front |
| Leitura | O front lê por Supabase client sob RLS; relatórios viram views/funções SQL |
| Importar e classificar | **Segue em Python**, como comando que o Thiago roda no computador dele e grava no Supabase por uma chave só dele. Não é reescrito em PL/pgSQL agora |
| Meu Pluggy | Depois do login: função agendada no Supabase, credenciais nos segredos do projeto, nunca no git nem no chat |
| Front | React + Vite como hoje, hospedado em Cloudflare Pages, PWA |

**Por que o importador fica em Python:** é onde mora a regra de dinheiro que tem os testes (classificação, repasse, duplicata, Pix no crédito). Reescrevê-lo junto com a troca de banco misturaria duas mudanças; se os números mudarem, não saberíamos qual causou. Portar para PL/pgSQL, como no Lifetrailer, fica como etapa posterior e **só com os mesmos testes**.

## Etapas (um PR cada)

1. **Esquema e RLS:** migrações SQL das tabelas, com `household_id`, e testes de isolamento (A nunca lê, grava ou apaga dado de B).
2. **Importador grava no Postgres:** mesma classificação, mesmos testes; a suíte atual é a prova de que os números não mudam.
3. **Relatórios em SQL:** o que `service.py` calcula hoje (gasto, receita, repasse, investimento, parcelas, assinaturas, orçamento), com paridade verificada contra o SQLite.
4. **Front no Supabase:** login e leitura sob RLS, deploy no Cloudflare Pages.
5. **Migração do banco real:** feita **pelo Thiago**, no computador dele. Nenhum extrato, banco ou chave passa pelo chat nem entra no git.
6. **Meu Pluggy agendado** e backup do Postgres com restauração testada.

## Requisitos de segurança

Todos os do ADR 0024 (falhar fechado, teste de isolamento, HTTPS, sem valor em log, segredos por variável de ambiente, backup com restauração testada) e, em especial:

- A chave `service_role` e qualquer segredo **nunca** vão para o git, o front ou o chat.
- Em toda tabela, RLS ligado; tabela sem política nega tudo.
- Os testes de isolamento rodam contra um Postgres de verdade, não contra mock.
- **Heartbeat diário** (como no Lifetrailer): uma tarefa agendada faz uma consulta leve, para o projeto gratuito não pausar por inatividade. O Meu Pluggy agendado também conta como atividade.

## Consequências

- O Arkhe deixa de ser "só local". README, ADR 0008 e CLAUDE.md passam a distinguir **uso local** (SQLite, `127.0.0.1`, como hoje) de **hospedado**; isso é editado junto das etapas, não antes.
- O uso local atual **continua funcionando** até a etapa 5, quando o Thiago decide a virada.
- Há duas implementações do relatório durante a transição (Python e SQL); a paridade da etapa 3 existe para isso.
- Custo e limites do plano gratuito do Supabase devem ser conferidos na hora; este ADR não assume valores. Projeto gratuito pode ser pausado por inatividade, o que pesa para um app financeiro.
- Dependência de terceiro: se o Supabase mudar preço ou termos, a saída é Postgres comum (as migrações são SQL puro).
