-- Arkhe Finance no Supabase (ADR 0025), etapa 1: esquema e isolamento por casa (RLS).
-- Dinheiro em centavos inteiros (bigint), como no ADR 0011. Casas separadas: cada pessoa
-- pertence a uma única casa e só enxerga o que é dela. Sem política, a tabela nega tudo.

create table public.households (
    id   uuid primary key default gen_random_uuid(),
    name text not null default ''
);

-- Um usuário pertence a exatamente uma casa (PK em user_id). Duas pessoas na mesma casa
-- compartilham o household_id; em casas separadas, cada uma tem o seu.
create table public.members (
    user_id      uuid primary key references auth.users (id) on delete cascade,
    household_id uuid not null references public.households (id) on delete cascade
);

-- A casa de quem está logado. security definer para a política de outras tabelas não
-- depender de ler members sob RLS.
create function public.minha_casa() returns uuid
    language sql stable security definer set search_path = public as
$$ select household_id from public.members where user_id = auth.uid() $$;
revoke all on function public.minha_casa() from public;
grant execute on function public.minha_casa() to authenticated;

create table public.transactions (
    id               bigint generated always as identity primary key,
    household_id     uuid not null default public.minha_casa() references public.households (id) on delete cascade,
    account          text not null,
    source_id        text not null,
    date             date not null,
    amount_cents     bigint not null,
    description      text not null,
    counterparty     text not null default '',
    kind             text not null,
    category         text not null,
    category_locked  boolean not null default false,
    dedupe_key       text not null,
    source           text not null default 'csv',
    external_id      text,
    operation_type   text,
    unique (household_id, dedupe_key)
);
create index idx_tx_date on public.transactions (household_id, date);

create table public.rules (
    id           bigint generated always as identity primary key,
    household_id uuid not null default public.minha_casa() references public.households (id) on delete cascade,
    pattern      text not null check (length(trim(pattern)) > 0),
    category     text not null,
    priority     integer not null default 0
);

create table public.budgets (
    household_id uuid not null default public.minha_casa() references public.households (id) on delete cascade,
    category     text not null,
    limit_cents  bigint not null check (limit_cents > 0),
    primary key (household_id, category)
);

create table public.own_names (
    household_id uuid not null default public.minha_casa() references public.households (id) on delete cascade,
    name         text not null,
    primary key (household_id, name)
);

-- Estado interno do importador; só a chave de serviço mexe.
create table public.meta (
    household_id uuid not null references public.households (id) on delete cascade,
    key          text not null,
    value        text not null,
    primary key (household_id, key)
);

-- RLS em toda tabela.
alter table public.households   enable row level security;
alter table public.members      enable row level security;
alter table public.transactions enable row level security;
alter table public.rules        enable row level security;
alter table public.budgets      enable row level security;
alter table public.own_names    enable row level security;
alter table public.meta         enable row level security;

-- Nada por padrão: quem não é service_role só recebe o que está listado abaixo.
revoke all on public.households, public.members, public.transactions, public.rules,
              public.budgets, public.own_names, public.meta from anon, authenticated;

grant select on public.households to authenticated;
create policy households_ler on public.households for select to authenticated
    using (id = public.minha_casa());

grant select on public.members to authenticated;
create policy members_ler on public.members for select to authenticated
    using (user_id = auth.uid());

-- Lançamentos: quem está logado lê os da sua casa e só muda a categoria. Criar e apagar
-- lançamento é do importador (service_role); household_id nunca muda por aqui.
grant select on public.transactions to authenticated;
grant update (category, category_locked) on public.transactions to authenticated;
create policy transactions_ler on public.transactions for select to authenticated
    using (household_id = public.minha_casa());
create policy transactions_categorizar on public.transactions for update to authenticated
    using (household_id = public.minha_casa())
    with check (household_id = public.minha_casa());

-- Regras, orçamentos e nomes próprios: CRUD só na própria casa.
grant select, insert, update, delete on public.rules     to authenticated;
grant select, insert, update, delete on public.budgets   to authenticated;
grant select, insert, update, delete on public.own_names to authenticated;
create policy rules_casa on public.rules for all to authenticated
    using (household_id = public.minha_casa()) with check (household_id = public.minha_casa());
create policy budgets_casa on public.budgets for all to authenticated
    using (household_id = public.minha_casa()) with check (household_id = public.minha_casa());
create policy own_names_casa on public.own_names for all to authenticated
    using (household_id = public.minha_casa()) with check (household_id = public.minha_casa());
-- identity: o front precisa do contador para inserir regra.
grant usage on sequence public.rules_id_seq to authenticated;

-- O importador (service_role) faz tudo, ignorando RLS.
grant all on public.households, public.members, public.transactions, public.rules,
             public.budgets, public.own_names, public.meta to service_role;
grant usage, select on all sequences in schema public to service_role;
