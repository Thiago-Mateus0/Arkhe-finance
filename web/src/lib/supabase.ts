import { createClient, type SupabaseClient } from "@supabase/supabase-js";

// Modo nuvem (ADR 0025): ligado só quando as duas variáveis existem na hora do build. A chave "anon"
// é pública por desenho; quem protege o dado é o RLS no banco. Sem elas, o app fala com a API local.
const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const chave = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

export const sb: SupabaseClient | null = url && chave ? createClient(url, chave) : null;
export const NUVEM = sb !== null;
