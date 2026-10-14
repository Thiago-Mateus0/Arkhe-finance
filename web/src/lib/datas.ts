const MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];

/** "2026-10" -> "Outubro 2026" */
export function nomeDoMes(ym: string): string {
  const [a, m] = ym.split("-").map(Number);
  const n = MESES[(m ?? 1) - 1] ?? "";
  return `${n.charAt(0).toUpperCase()}${n.slice(1)} ${a}`;
}
/** "2026-10" -> "Out 2026" */
export const mesCurto = (ym: string): string => {
  const [a, m] = ym.split("-").map(Number);
  return `${(MESES[(m ?? 1) - 1] ?? "").slice(0, 3).replace(/^./, (c) => c.toUpperCase())} ${a}`;
};
export const saudacao = (h = new Date().getHours()): string => (h < 12 ? "Bom dia" : h < 18 ? "Boa tarde" : "Boa noite");

/** "2026-10-14" -> "Hoje" | "Ontem" | "14 out" */
export function rotuloDoDia(iso: string, hoje = new Date()): string {
  const [a, m, d] = iso.split("-").map(Number);
  const dia = new Date(a!, m! - 1, d!);
  const base = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
  const dif = Math.round((base.getTime() - dia.getTime()) / 86_400_000);
  if (dif === 0) return "Hoje";
  if (dif === 1) return "Ontem";
  return `${d} ${(MESES[m! - 1] ?? "").slice(0, 3)}`;
}
