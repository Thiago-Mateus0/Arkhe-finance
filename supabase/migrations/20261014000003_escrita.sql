-- Arkhe Finance no Supabase (ADR 0025), etapa 4: o que o front escreve, com a mesma regra do Python.
-- Roda com os direitos de quem chama (RLS e as permissões de coluna valem).

-- Categorias conhecidas (de regras e de lançamentos), sem "Sem categoria", em ordem de código.
create function public.categorias() returns jsonb
    language sql stable as
$$
select coalesce(jsonb_agg(c order by c collate "C"), '[]'::jsonb)
from (select category as c from public.rules where household_id = public.minha_casa()
      union
      select category from public.transactions where household_id = public.minha_casa()) s
where c <> 'Sem categoria'
$$;

-- Recalcula a categoria dos lançamentos não travados: o padrão (substring, sem caixa) de maior
-- prioridade vence; empate vai para o padrão mais longo; depois a regra mais antiga (rules.py).
create function public.recategorizar() returns integer
    language plpgsql as
$$
declare n integer;
begin
    update public.transactions t
       set category = coalesce((
            select r.category from public.rules r
            where r.household_id = public.minha_casa()
              and position(lower(r.pattern) in lower(t.description || ' ' || t.counterparty)) > 0
            order by r.priority desc, length(r.pattern) desc, r.id asc
            limit 1), 'Sem categoria')
     where t.household_id = public.minha_casa() and not t.category_locked;
    get diagnostics n = row_count;
    return n;
end
$$;

-- Categoria manual: fica travada. Com lembrar, cria uma regra pela contraparte (ou descrição),
-- prioridade 5, e recategoriza o resto. Devolve null se o lançamento não é da sua casa.
create function public.categorizar(tx_id bigint, categoria text, lembrar boolean default false) returns jsonb
    language plpgsql as
$$
declare
    t record;
    padrao text;
begin
    if btrim(categoria) = '' then
        raise exception 'Categoria vazia';
    end if;
    select description, counterparty into t from public.transactions
        where id = tx_id and household_id = public.minha_casa();
    if not found then
        return null;
    end if;
    update public.transactions set category = categoria, category_locked = true where id = tx_id;
    if lembrar then
        padrao := lower(coalesce(nullif(t.counterparty, ''), t.description));
        insert into public.rules (pattern, category, priority) values (padrao, categoria, 5);
    end if;
    return jsonb_build_object('categoria', categoria, 'regra_criada', padrao,
                              'recategorizadas', case when lembrar then public.recategorizar() else 0 end);
end
$$;

revoke all on function public.categorias(), public.recategorizar(), public.categorizar(bigint, text, boolean)
    from public, anon;
grant execute on function public.categorias(), public.recategorizar(), public.categorizar(bigint, text, boolean)
    to authenticated;
