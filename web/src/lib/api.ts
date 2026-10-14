export async function api<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) {
    const e = (await r.json().catch(() => ({}))) as { detail?: string };
    throw new Error(e.detail || `Erro ${r.status}`);
  }
  return r.json() as Promise<T>;
}

export interface CategoriaMes { categoria: string; valor: number; qtd: number; mes_anterior: number }
export interface Monthly {
  mes: string; gastos_total: number; gastos_mes_anterior: number; gastos_cartao: number; gastos_conta: number;
  receitas_total: number; por_categoria: CategoriaMes[];
}
export interface Daily { mes: string; dias: { dia: number; gastos: number; entradas: number }[] }
export interface Budgets {
  mes: string; orcado_total: number; gasto_nas_categorias: number;
  itens: { categoria: string; limite: number; gasto: number; restante: number; percentual: number; estado: "ok" | "atencao" | "estourou" }[];
}
export interface Parcelas { meses: { mes: string; total: number; itens: unknown[] }[]; total: number }
export interface Assinaturas { mes: string; total: number; itens: { nome: string; ultimo_valor: number; proxima: string | null }[] }
export interface Tx { id: number; date: string; amount_cents: number; description: string; category: string; kind: string }
