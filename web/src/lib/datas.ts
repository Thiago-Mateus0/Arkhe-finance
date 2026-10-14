const MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
const DIAS = ["domingo", "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado"];
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

export const mesAtual = (hoje = new Date()): string => `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, "0")}`;
/** "2026-10" -> "Outubro 2026" */
export function nomeDoMes(ym: string): string {
  const [a, m] = ym.split("-").map(Number);
  return `${cap(MESES[(m ?? 1) - 1] ?? "")} ${a}`;
}
/** "2026-10" -> "Out 2026" */
export const mesCurto = (ym: string): string => {
  const [a, m] = ym.split("-").map(Number);
  return `${cap((MESES[(m ?? 1) - 1] ?? "").slice(0, 3))} ${a}`;
};
/** "2026-10" -> "outubro" */
export const soMes = (ym: string): string => MESES[Number(ym.slice(5)) - 1] ?? "";
export const saudacao = (h = new Date().getHours()): string => (h < 12 ? "Bom dia" : h < 18 ? "Boa tarde" : "Boa noite");

const partes = (iso: string) => { const [a, m, d] = iso.split("-").map(Number); return new Date(a!, m! - 1, d!); };
export const diaCurto = (iso: string): string => { const d = partes(iso); return `${d.getDate()} de ${(MESES[d.getMonth()] ?? "").slice(0, 3)}`; };

/** "Hoje", "Ontem", dia da semana (últimos 6 dias) ou "5 de out". */
export function rotuloDoDia(iso: string, hoje = new Date()): string {
  const d = partes(iso);
  const base = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
  const dif = Math.round((base.getTime() - d.getTime()) / 86_400_000);
  if (dif === 0) return "Hoje";
  if (dif === 1) return "Ontem";
  if (dif > 1 && dif < 7) return cap(DIAS[d.getDay()] ?? "");
  return diaCurto(iso);
}
