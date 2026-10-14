import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { useApp } from "./contexto";

type Estado<T> = { fase: "carregando" } | { fase: "erro"; msg: string } | { fase: "ok"; dados: T };

/** GET com recarga automática quando o app invalida (importar, categorizar, salvar limite...). */
export function useApi<T>(url: string | null) {
  const { versao } = useApp();
  const [estado, setEstado] = useState<Estado<T>>({ fase: "carregando" });
  const [tentativa, setTentativa] = useState(0);
  const recarregar = useCallback(() => setTentativa((n) => n + 1), []);

  useEffect(() => {
    if (!url) return;
    let vivo = true;
    setEstado((e) => (e.fase === "ok" ? e : { fase: "carregando" })); // mantém o que já tem enquanto atualiza
    api<T>(url)
      .then((dados) => vivo && setEstado({ fase: "ok", dados }))
      .catch((e: Error) => vivo && setEstado({ fase: "erro", msg: e.message }));
    return () => { vivo = false; };
  }, [url, versao, tentativa]);

  return { estado, recarregar };
}
