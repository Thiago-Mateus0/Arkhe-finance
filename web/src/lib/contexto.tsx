import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "./api";
import { mesAtual } from "./datas";
import { gravarPref, lerPref } from "./preferencias";
import { hrefDe, lerHash, type Local, type Rota } from "./rotas";

type Tema = "dark" | "light";

interface App {
  meses: string[]; mes: string | null; setMes: (m: string) => void; erroMeses: string | null; recarregarMeses: () => void;
  oculto: boolean; alternarOculto: () => void; tema: Tema; alternarTema: () => void;
  versao: number; invalidar: () => void;
  local: Local; ir: (rota: Rota, params?: Record<string, string | undefined>) => void;
}
const Ctx = createContext<App | null>(null);
export const useApp = (): App => {
  const c = useContext(Ctx);
  if (!c) throw new Error("useApp fora do provedor");
  return c;
};

export function Provedor({ children }: { children: ReactNode }) {
  const [meses, setMeses] = useState<string[]>([]);
  const [mes, setMes] = useState<string | null>(null);
  const [erroMeses, setErroMeses] = useState<string | null>(null);
  const [oculto, setOculto] = useState<boolean>(() => lerPref("hidden", false));
  const [tema, setTema] = useState<Tema>(() => (lerPref<string>("theme", "dark") === "light" ? "light" : "dark"));
  const [versao, setVersao] = useState(0);
  const [local, setLocal] = useState<Local>(() => lerHash());
  const [carga, setCarga] = useState(0);

  useEffect(() => {
    api<string[]>("/months")
      .then((m) => {
        // O mês atual sempre existe na lista, para o "mês sem lançamentos" poder ser visto e explicado.
        const lista = m.includes(mesAtual()) ? m : [mesAtual(), ...m];
        setMeses(lista);
        setMes((atual) => atual ?? m[0] ?? lista[0] ?? null); // abre no mês mais recente com lançamentos
        setErroMeses(null);
      })
      .catch((e: Error) => setErroMeses(e.message));
  }, [carga]);

  useEffect(() => {
    const aoMudar = () => { setLocal(lerHash()); window.scrollTo(0, 0); };
    window.addEventListener("hashchange", aoMudar);
    return () => window.removeEventListener("hashchange", aoMudar);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = tema;
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", tema === "light" ? "#f3f2ee" : "#000000");
  }, [tema]);

  const valor = useMemo<App>(() => ({
    meses, mes, setMes, erroMeses, recarregarMeses: () => setCarga((n) => n + 1),
    oculto, alternarOculto: () => setOculto((o) => { gravarPref("hidden", !o); return !o; }),
    tema, alternarTema: () => setTema((t) => { const n = t === "dark" ? "light" : "dark"; gravarPref("theme", n); return n; }),
    versao, invalidar: () => setVersao((n) => n + 1),
    local, ir: (rota, params) => { location.hash = hrefDe(rota, params); },
  }), [meses, mes, erroMeses, oculto, tema, versao, local]);

  const setMesEstavel = useCallback((m: string) => setMes(m), []);
  return <Ctx.Provider value={{ ...valor, setMes: setMesEstavel }}>{children}</Ctx.Provider>;
}
