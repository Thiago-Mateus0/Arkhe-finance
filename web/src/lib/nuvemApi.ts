import type { SupabaseClient } from "@supabase/supabase-js";

/**
 * As mesmas rotas da API local, atendidas pelo Supabase (ADR 0025). As telas não sabem a diferença:
 * os relatórios são funções SQL com o mesmo JSON, e o isolamento por casa é do banco (RLS).
 */
const SEM_CATEGORIA = "Sem categoria";

const falha = (e: { message: string } | null) => { if (e) throw new Error(e.message); };

export function proximoMes(m: string): string {
  const [a, n] = m.split("-").map(Number);
  return n === 12 ? `${a + 1}-01` : `${a}-${String(n + 1).padStart(2, "0")}`;
}

/** Remove o que quebraria o filtro `or=(...)` do PostgREST (vírgula, parênteses, curingas). */
export function termoDeBusca(q: string): string {
  return q.trim().toLowerCase().replace(/[,()*%\\]/g, " ").replace(/\s+/g, " ").trim();
}

export async function nuvemApi<T>(sb: SupabaseClient, url: string, init?: RequestInit): Promise<T> {
  const metodo = (init?.method ?? "GET").toUpperCase();
  const u = new URL(url, "http://local");
  const p = u.searchParams;
  const caminho = u.pathname;
  const corpo = typeof init?.body === "string" ? (JSON.parse(init.body) as Record<string, unknown>) : {};

  const rpc = async (nome: string, args?: Record<string, unknown>) => {
    const { data, error } = await sb.rpc(nome, args);
    falha(error);
    return data;
  };
  const m = (re: RegExp) => caminho.match(re);
  const out = (v: unknown) => v as T;

  if (metodo === "GET") {
    if (caminho === "/months") return out(await rpc("meses_com_dados"));
    if (caminho === "/categories") return out(await rpc("categorias"));
    if (caminho === "/reports/monthly") return out(await rpc("relatorio_mensal", { mes: p.get("month") }));
    if (caminho === "/reports/daily") return out(await rpc("relatorio_diario", { mes: p.get("month") }));
    if (caminho === "/budgets") return out(await rpc("orcamento_status", { mes: p.get("month") }));
    if (caminho === "/reports/assinaturas") return out(await rpc("assinaturas_do_mes", { mes: p.get("month") }));
    if (caminho === "/reports/parcelas") return out(await rpc("parcelas_a_vir"));
    if (caminho === "/rules") {
      const { data, error } = await sb.from("rules").select("id,pattern,category,priority").order("id");
      falha(error);
      return out(data);
    }
    if (caminho === "/transactions") {
      const mes = p.get("month") ?? "";
      let q = sb.from("transactions")
        .select("id,date,amount_cents,description,counterparty,account,category,kind,category_locked")
        .gte("date", `${mes}-01`).lt("date", `${proximoMes(mes)}-01`);
      const cat = p.get("category");
      if (cat) q = q.eq("category", cat);
      const tipos = (p.get("kinds") ?? p.get("kind") ?? "").split(",").filter(Boolean);
      if (tipos.length) q = q.in("kind", tipos);
      const busca = termoDeBusca(p.get("q") ?? "");
      if (busca) q = q.or(`description.ilike.*${busca}*,counterparty.ilike.*${busca}*`);
      const desc = p.get("desc") === "true";
      const { data, error } = await q.order("date", { ascending: !desc }).order("id", { ascending: !desc }).range(0, 4999);
      falha(error);
      return out((data ?? []).map((r) => ({ ...r, category_locked: Number(r.category_locked) })));
    }
  }

  const regra = m(/^\/rules\/(\d+)$/);
  if (caminho === "/rules" && metodo === "POST" || regra && metodo === "PUT") {
    const pattern = String(corpo.pattern ?? "").trim();
    const category = String(corpo.category ?? "").trim();
    if (!pattern || !category) throw new Error("Padrão e categoria são obrigatórios");
    const linha = { pattern, category, priority: Number(corpo.priority ?? 0) };
    if (regra) {
      const { data, error } = await sb.from("rules").update(linha).eq("id", Number(regra[1])).select("id");
      falha(error);
      if (!data?.length) throw new Error("Regra não encontrada");
    } else {
      falha((await sb.from("rules").insert(linha)).error);
    }
    return out({ recategorizadas: await rpc("recategorizar") });
  }
  if (regra && metodo === "DELETE") {
    const { data, error } = await sb.from("rules").delete().eq("id", Number(regra[1])).select("id");
    falha(error);
    if (!data?.length) throw new Error("Regra não encontrada");
    await rpc("recategorizar");
    return out({ ok: true });
  }

  const tx = m(/^\/transactions\/(\d+)$/);
  if (tx && metodo === "PATCH") {
    const categoria = String(corpo.category ?? "").trim();
    if (!categoria) throw new Error("Categoria vazia");
    const r = await rpc("categorizar", { tx_id: Number(tx[1]), categoria, lembrar: Boolean(corpo.remember) });
    if (r === null) throw new Error("Transação não encontrada");
    return out(r);
  }

  const orc = m(/^\/budgets\/(.+)$/);
  if (orc && metodo === "PUT") {
    const categoria = decodeURIComponent(orc[1]).trim();
    const limite = Number(corpo.limite);
    if (!categoria || categoria.length > 60) throw new Error("Categoria inválida (vazia ou com mais de 60 caracteres)");
    if (categoria === SEM_CATEGORIA) throw new Error("Não dá para orçar 'Sem categoria': classifique os lançamentos antes");
    if (!(limite > 0)) throw new Error("O limite precisa ser maior que zero");
    const { error } = await sb.from("budgets")
      .upsert({ category: categoria, limit_cents: Math.round(limite * 100) }, { onConflict: "household_id,category" });
    falha(error);
    return out({ categoria, limite });
  }
  if (orc && metodo === "DELETE") {
    const { data, error } = await sb.from("budgets").delete().eq("category", decodeURIComponent(orc[1]).trim()).select("category");
    falha(error);
    if (!data?.length) throw new Error("Orçamento não encontrado");
    return out({ ok: true });
  }

  if (caminho === "/import") {
    throw new Error("Importar pela nuvem ainda não está disponível no celular. Importe no computador: python -m financas nuvem import");
  }
  throw new Error(`Rota sem suporte na nuvem: ${metodo} ${caminho}`);
}
