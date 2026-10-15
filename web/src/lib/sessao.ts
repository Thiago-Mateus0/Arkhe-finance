import { useEffect, useState } from "react";
import { sb } from "./supabase";

export type Sessao = "carregando" | "entrou" | "fora";

/** Estado do login no modo nuvem. A sessão fica guardada pelo próprio Supabase neste aparelho. */
export function useSessao(): Sessao {
  const [s, setS] = useState<Sessao>("carregando");
  useEffect(() => {
    if (!sb) return;
    void sb.auth.getSession().then(({ data }) => setS(data.session ? "entrou" : "fora"));
    const { data } = sb.auth.onAuthStateChange((_e, sessao) => setS(sessao ? "entrou" : "fora"));
    return () => data.subscription.unsubscribe();
  }, []);
  return s;
}

export const sair = () => { void sb?.auth.signOut(); };
