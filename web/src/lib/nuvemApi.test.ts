import { describe, expect, it } from "vitest";
import type { SupabaseClient } from "@supabase/supabase-js";
import { nuvemApi, proximoMes, termoDeBusca } from "./nuvemApi";

/** Cliente falso: registra cada chamada e devolve o que o teste mandar. */
function falso(resposta: { data?: unknown; error?: { message: string } | null } = {}) {
  const chamadas: [string, ...unknown[]][] = [];
  const res = { data: resposta.data ?? null, error: resposta.error ?? null };
  const cadeia: Record<string, unknown> = {};
  const metodos = ["select", "insert", "update", "delete", "upsert", "eq", "gte", "lt", "in", "or", "order", "range"];
  for (const m of metodos) cadeia[m] = (...a: unknown[]) => { chamadas.push([m, ...a]); return cadeia; };
  cadeia.then = (ok: (v: unknown) => unknown) => Promise.resolve(res).then(ok);
  const sb = {
    rpc: (nome: string, args?: unknown) => { chamadas.push(["rpc", nome, args]); return Promise.resolve(res); },
    from: (t: string) => { chamadas.push(["from", t]); return cadeia; },
  } as unknown as SupabaseClient;
  return { sb, chamadas };
}

describe("rotas de leitura", () => {
  it("relatório mensal chama a função SQL com o mês", async () => {
    const { sb, chamadas } = falso({ data: { mes: "2026-09" } });
    await nuvemApi(sb, "/reports/monthly?month=2026-09");
    expect(chamadas).toEqual([["rpc", "relatorio_mensal", { mes: "2026-09" }]]);
  });

  it("lançamentos do mês: intervalo [dia 1, mês seguinte), tipos, ordem e categoria_locked numérica", async () => {
    const { sb, chamadas } = falso({ data: [{ id: 1, category_locked: true }, { id: 2, category_locked: false }] });
    const r = await nuvemApi<{ category_locked: number }[]>(
      sb, "/transactions?month=2026-12&kinds=income,expense&desc=true&category=Mercado");
    expect(r.map((x) => x.category_locked)).toEqual([1, 0]);
    const nomes = chamadas.map((c) => c[0]);
    expect(chamadas).toContainEqual(["gte", "date", "2026-12-01"]);
    expect(chamadas).toContainEqual(["lt", "date", "2027-01-01"]); // virada de ano
    expect(chamadas).toContainEqual(["in", "kind", ["income", "expense"]]);
    expect(chamadas).toContainEqual(["eq", "category", "Mercado"]);
    expect(chamadas).toContainEqual(["order", "date", { ascending: false }]);
    expect(nomes).not.toContain("or");
  });

  it("busca limpa os caracteres que quebrariam o filtro", async () => {
    const { sb, chamadas } = falso({ data: [] });
    await nuvemApi(sb, `/transactions?month=2026-09&q=${encodeURIComponent("a,b) or (id.gt.0")}`);
    const filtro = chamadas.find((c) => c[0] === "or")![1] as string;
    expect(filtro).toBe("description.ilike.*a b or id.gt.0*,counterparty.ilike.*a b or id.gt.0*");
    expect(filtro).not.toMatch(/[()]/);
  });
});

describe("escrita", () => {
  it("categoria manual vira a função categorizar", async () => {
    const { sb, chamadas } = falso({ data: { categoria: "Lazer", recategorizadas: 0 } });
    await nuvemApi(sb, "/transactions/42", { method: "PATCH", body: JSON.stringify({ category: "Lazer", remember: true }) });
    expect(chamadas).toEqual([["rpc", "categorizar", { tx_id: 42, categoria: "Lazer", lembrar: true }]]);
  });

  it("lançamento de outra casa (função devolve null) vira erro 'não encontrada'", async () => {
    const { sb } = falso({ data: null });
    await expect(nuvemApi(sb, "/transactions/7", { method: "PATCH", body: JSON.stringify({ category: "X" }) }))
      .rejects.toThrow("Transação não encontrada");
  });

  it("regra com padrão vazio é recusada antes de ir ao banco", async () => {
    const { sb, chamadas } = falso();
    await expect(nuvemApi(sb, "/rules", { method: "POST", body: JSON.stringify({ pattern: "  ", category: "X" }) }))
      .rejects.toThrow("obrigatórios");
    expect(chamadas).toEqual([]);
  });

  it("regra nova insere e recategoriza", async () => {
    const { sb, chamadas } = falso({ data: 3 });
    await nuvemApi(sb, "/rules", { method: "POST", body: JSON.stringify({ pattern: " padaria ", category: "Mercado", priority: 5 }) });
    expect(chamadas).toContainEqual(["insert", { pattern: "padaria", category: "Mercado", priority: 5 }]);
    expect(chamadas).toContainEqual(["rpc", "recategorizar", undefined]);
  });

  it("orçamento: centavos exatos, e recusa limite inválido e 'Sem categoria'", async () => {
    const { sb, chamadas } = falso();
    await nuvemApi(sb, "/budgets/Delivery", { method: "PUT", body: JSON.stringify({ limite: 150.5 }) });
    expect(chamadas).toContainEqual(["upsert", { category: "Delivery", limit_cents: 15050 }, { onConflict: "household_id,category" }]);
    await nuvemApi(sb, "/budgets/Lazer", { method: "PUT", body: JSON.stringify({ limite: 1.15 }) }); // 1.15*100 em float dá 114.99…
    expect(chamadas).toContainEqual(["upsert", { category: "Lazer", limit_cents: 115 }, { onConflict: "household_id,category" }]);
    await expect(nuvemApi(sb, "/budgets/Delivery", { method: "PUT", body: JSON.stringify({ limite: 0 }) })).rejects.toThrow("maior que zero");
    await expect(nuvemApi(sb, "/budgets/Sem%20categoria", { method: "PUT", body: JSON.stringify({ limite: 10 }) })).rejects.toThrow("Sem categoria");
  });

  it("erro do banco chega como mensagem", async () => {
    const { sb } = falso({ error: { message: "permission denied" } });
    await expect(nuvemApi(sb, "/months")).rejects.toThrow("permission denied");
  });

  it("importar pela nuvem explica o que fazer", async () => {
    const { sb } = falso();
    await expect(nuvemApi(sb, "/import", { method: "POST", body: new FormData() })).rejects.toThrow("no computador");
  });
});

describe("auxiliares", () => {
  it("proximoMes vira o ano", () => {
    expect(proximoMes("2026-01")).toBe("2026-02");
    expect(proximoMes("2026-12")).toBe("2027-01");
  });
  it("termoDeBusca", () => {
    expect(termoDeBusca("  Padaria,  (X) ")).toBe("padaria x");
  });
});
