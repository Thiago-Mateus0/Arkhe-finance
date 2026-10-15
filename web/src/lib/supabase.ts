import { createClient, type SupabaseClient } from "@supabase/supabase-js";

// Modo nuvem (ADR 0025): ligado só quando as duas variáveis existem na hora do build. A chave "anon"
// é pública por desenho; quem protege o dado é o RLS no banco. Sem elas, o app fala com a API local.
const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const chave = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

/** O cliente quer só `https://codigo.supabase.co`. Quem cola a URL da Data API (`.../rest/v1/`) ou com
 * barra no fim recebe "Invalid path specified in request URL"; aqui ficamos só com a origem. */
export function origemDoSupabase(bruta: string): string {
  try { return new URL(bruta.trim()).origin; } catch { return bruta.trim(); }
}

export const sb: SupabaseClient | null = url && chave ? createClient(origemDoSupabase(url), chave.trim()) : null;
export const NUVEM = sb !== null;
