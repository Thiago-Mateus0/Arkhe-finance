export type Rota = "inicio" | "atividades" | "gastos" | "orcamento" | "fluxo" | "regras" | "importar";
const ROTAS: Rota[] = ["inicio", "atividades", "gastos", "orcamento", "fluxo", "regras", "importar"];

export interface Local { rota: Rota; params: URLSearchParams }

/** "#/atividades?cat=Delivery" -> { rota: "atividades", params } */
export function lerHash(hash: string = location.hash): Local {
  const [caminho = "", busca = ""] = hash.replace(/^#\/?/, "").split("?");
  const rota = ROTAS.find((r) => r === caminho) ?? "inicio";
  return { rota, params: new URLSearchParams(busca) };
}
export function hrefDe(rota: Rota, params?: Record<string, string | undefined>): string {
  const q = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([k, v]) => { if (v) q.set(k, v); });
  const s = q.toString();
  return `#/${rota}${s ? `?${s}` : ""}`;
}
