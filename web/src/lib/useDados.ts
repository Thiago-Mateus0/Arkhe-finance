import { useCallback, useEffect, useState } from "react";
import { api, type Assinaturas, type Budgets, type Daily, type Monthly, type Parcelas, type Tx } from "./api";

export interface Dados {
  rep: Monthly; daily: Daily; bud: Budgets; parc: Parcelas; ass: Assinaturas; tx: Tx[];
}

type Estado = { fase: "carregando" } | { fase: "erro"; msg: string } | { fase: "ok"; dados: Dados };

/** Tudo que o Início precisa para um mês, buscado em paralelo. */
export function useDados(mes: string | null) {
  const [estado, setEstado] = useState<Estado>({ fase: "carregando" });
  const [tentativa, setTentativa] = useState(0);
  const recarregar = useCallback(() => setTentativa((n) => n + 1), []);

  useEffect(() => {
    if (!mes) return;
    let vivo = true;
    setEstado({ fase: "carregando" });
    const q = `month=${encodeURIComponent(mes)}`;
    Promise.all([
      api<Monthly>(`/reports/monthly?${q}`),
      api<Daily>(`/reports/daily?${q}`),
      api<Budgets>(`/budgets?${q}`),
      api<Parcelas>("/reports/parcelas"),
      api<Assinaturas>(`/reports/assinaturas?${q}`),
      api<Tx[]>(`/transactions?${q}&kinds=income,expense&desc=true`),
    ])
      .then(([rep, daily, bud, parc, ass, tx]) => vivo && setEstado({ fase: "ok", dados: { rep, daily, bud, parc, ass, tx } }))
      .catch((e: Error) => vivo && setEstado({ fase: "erro", msg: e.message }));
    return () => { vivo = false; };
  }, [mes, tentativa]);

  return { estado, recarregar };
}
