-- Arkhe Finance no Supabase (ADR 0025), etapa 3: relatórios em SQL, com o mesmo formato JSON da API local.
-- Todas as funções rodam com os direitos de quem chama (RLS vale) e ainda filtram por minha_casa().
-- Centavos inteiros até a borda: o valor em reais só aparece na divisão por 100 do JSON.

create function public.meses_com_dados() returns jsonb
    language sql stable as
$$
select coalesce(jsonb_agg(m order by m desc), '[]'::jsonb)
from (select distinct to_char(date, 'YYYY-MM') as m
      from public.transactions where household_id = public.minha_casa()) s
$$;

create function public.relatorio_mensal(mes text) returns jsonb
    language sql stable as
$$
with t as (select * from public.transactions where household_id = public.minha_casa()),
atual as (
    select category, -sum(amount_cents) as c, count(*) as n from t
    where to_char(date, 'YYYY-MM') = mes and kind = 'expense' group by category),
ant as (
    select category, -sum(amount_cents) as c from t
    where to_char(date, 'YYYY-MM') = to_char(to_date(mes || '-01', 'YYYY-MM-DD') - interval '1 month', 'YYYY-MM')
      and kind = 'expense' group by category),
por_conta as (
    select account, -sum(amount_cents) as c from t
    where to_char(date, 'YYYY-MM') = mes and kind = 'expense' group by account)
select jsonb_build_object(
    'mes', mes,
    'gastos_total', coalesce((select sum(c) from atual), 0) / 100.0,
    'gastos_mes_anterior', coalesce((select sum(c) from ant), 0) / 100.0,
    'gastos_cartao', coalesce((select c from por_conta where account = 'nubank_fatura'), 0) / 100.0,
    'gastos_conta', coalesce((select c from por_conta where account = 'nubank_conta'), 0) / 100.0,
    'receitas_total', coalesce((select sum(amount_cents) from t
                                where to_char(date, 'YYYY-MM') = mes and kind = 'income'), 0) / 100.0,
    'por_categoria', coalesce((
        select jsonb_agg(jsonb_build_object('categoria', a.category, 'valor', a.c / 100.0, 'qtd', a.n,
                                            'mes_anterior', coalesce(p.c, 0) / 100.0)
                         order by a.c desc, a.category collate "C")
        from atual a left join ant p using (category)), '[]'::jsonb))
$$;

create function public.relatorio_diario(mes text) returns jsonb
    language sql stable as
$$
with base as (
    select date, kind, abs(amount_cents) as c from public.transactions
    where household_id = public.minha_casa() and kind in ('expense', 'income')),
ini as (select to_date(mes || '-01', 'YYYY-MM-DD') as d),
ant as (select (select d from ini) - interval '1 month' as d)
select jsonb_build_object(
    'mes', mes,
    'dias', (select jsonb_agg(jsonb_build_object(
                'dia', dia,
                'gastos', coalesce((select sum(c) from base where to_char(date, 'YYYY-MM') = mes
                                    and kind = 'expense' and extract(day from date) = dia), 0) / 100.0,
                'entradas', coalesce((select sum(c) from base where to_char(date, 'YYYY-MM') = mes
                                      and kind = 'income' and extract(day from date) = dia), 0) / 100.0)
                order by dia)
             from generate_series(1, extract(day from (select d from ini) + interval '1 month' - interval '1 day')::int) dia),
    'anterior', (select jsonb_agg(jsonb_build_object(
                'dia', dia,
                'gastos', coalesce((select sum(c) from base
                                    where to_char(date, 'YYYY-MM') = to_char((select d from ant), 'YYYY-MM')
                                      and kind = 'expense' and extract(day from date) = dia), 0) / 100.0)
                order by dia)
             from generate_series(1, extract(day from (select d from ant) + interval '1 month' - interval '1 day')::int) dia))
$$;

-- Orçamento (ADR 0015): estado em inteiros (80% do limite é gasto*5 >= limite*4); o percentual
-- mostrado arredonda meio para cima em décimos, em inteiros, igual ao Python.
create function public.orcamento_status(mes text) returns jsonb
    language sql stable as
$$
with gasto as (
    select category, -sum(amount_cents) as g from public.transactions
    where household_id = public.minha_casa() and to_char(date, 'YYYY-MM') = mes and kind = 'expense'
    group by category),
b as (
    select bu.category, bu.limit_cents as l, coalesce(g.g, 0) as g
    from public.budgets bu left join gasto g using (category)
    where bu.household_id = public.minha_casa()),
i as (
    select *,
           case when g > l then 'estourou' when g * 5 >= l * 4 then 'atencao' else 'ok' end as estado,
           case when g > l then 0 when g * 5 >= l * 4 then 1 else 2 end as ord
    from b)
select jsonb_build_object(
    'mes', mes,
    'orcado_total', coalesce((select sum(l) from b), 0) / 100.0,
    'gasto_nas_categorias', coalesce((select sum(g) from b), 0) / 100.0,
    'itens', coalesce((
        select jsonb_agg(jsonb_build_object(
            'categoria', category, 'limite', l / 100.0, 'gasto', g / 100.0, 'restante', (l - g) / 100.0,
            'percentual', floor((g * 2000 + l)::numeric / (2 * l)) / 10.0, 'estado', estado)
            order by ord, g::numeric / l desc, category collate "C")
        from i), '[]'::jsonb))
$$;

-- Assinaturas (ADR 0019): categoria "Assinaturas", ativa se cobrou no mês pedido ou nos 2 anteriores.
create function public.assinaturas_do_mes(mes text) returns jsonb
    language sql stable as
$$
with linhas as (
    select id, date, amount_cents,
           upper(trim(both ' ' from regexp_replace(
               coalesce(nullif(counterparty, ''), description), '\s+', ' ', 'g'))) as nome
    from public.transactions
    where household_id = public.minha_casa() and kind = 'expense' and category = 'Assinaturas'
      and date < (to_date(mes || '-01', 'YYYY-MM-DD') + interval '1 month')::date),
cobr as (select * from linhas where amount_cents < 0),  -- estorno entra no total, não vira assinatura
ult as (select distinct on (nome) nome, date, amount_cents from cobr order by nome, date desc, id asc),
qtd as (select nome, count(distinct to_char(date, 'YYYY-MM')) as m from cobr group by nome)
select jsonb_build_object(
    'mes', mes,
    'total', coalesce((select sum(-amount_cents) from linhas where to_char(date, 'YYYY-MM') = mes), 0) / 100.0,
    'itens', coalesce((
        select jsonb_agg(jsonb_build_object(
            'nome', u.nome, 'ultima_data', to_char(u.date, 'YYYY-MM-DD'),
            'ultimo_valor', -u.amount_cents / 100.0, 'meses', q.m,
            'proxima', case when q.m >= 2 then to_char((u.date + interval '1 month')::date, 'YYYY-MM-DD') end)
            order by u.amount_cents asc, u.nome collate "C")
        from ult u join qtd q using (nome)
        where to_char(u.date, 'YYYY-MM') >=
              to_char(to_date(mes || '-01', 'YYYY-MM-DD') - interval '2 months', 'YYYY-MM')), '[]'::jsonb))
$$;

-- Parcelas a vir (ADR 0012): projeta as que faltam depois da mais recente vista, só para meses
-- depois do último importado. O texto da fatura é não confiável: até 60 parcelas, 1 a 3 dígitos.
create function public.parcelas_a_vir() returns jsonb
    language sql stable as
$$
with f as (
    select date, amount_cents, regexp_replace(trim(both ' ' from description), '\s+', ' ', 'g') as d
    from public.transactions
    where household_id = public.minha_casa() and account = 'nubank_fatura' and kind = 'expense'),
hor as (select to_char(max(date), 'YYYY-MM') as h from f),
p as (
    select date, amount_cents,
           regexp_match(d, '^(.+?)\s-\s(?:Parcela\s+)?(\d{1,3})/(\d{1,3})\s*$', 'i') as m
    from f where amount_cents < 0),
v as (select date, amount_cents, m[1] as titulo, m[2]::int as n, m[3]::int as total from p where m is not null),
ok as (select * from v where n >= 1 and n < total and total <= 60),
g as (select upper(titulo) as k, total, amount_cents, max(n) as ultima
      from ok group by upper(titulo), total, amount_cents),
r as (
    select ok.date, ok.titulo, ok.amount_cents, ok.total, g.ultima
    from ok join g on upper(ok.titulo) = g.k and ok.total = g.total
                  and ok.amount_cents = g.amount_cents and ok.n = g.ultima),
proj as (
    select to_char(r.date + make_interval(months => k), 'YYYY-MM') as mes, r.titulo,
           -r.amount_cents as c, (r.ultima + k) || '/' || r.total as parcela
    from r, generate_series(1, r.total - r.ultima) k),
fut as (select * from proj where mes > (select h from hor))
select jsonb_build_object(
    'meses', coalesce((
        select jsonb_agg(jsonb_build_object('mes', mes, 'total', t / 100.0, 'itens', itens) order by mes)
        from (select mes, sum(c) as t,
                     jsonb_agg(jsonb_build_object('titulo', titulo, 'valor', c / 100.0, 'parcela', parcela)
                               order by titulo collate "C", parcela) as itens
              from fut group by mes) s), '[]'::jsonb),
    'total', coalesce((select sum(c) from fut), 0) / 100.0)
$$;

revoke all on function public.meses_com_dados(), public.relatorio_mensal(text), public.relatorio_diario(text),
    public.orcamento_status(text), public.assinaturas_do_mes(text), public.parcelas_a_vir() from public, anon;
grant execute on function public.meses_com_dados(), public.relatorio_mensal(text), public.relatorio_diario(text),
    public.orcamento_status(text), public.assinaturas_do_mes(text), public.parcelas_a_vir() to authenticated;
