import { useState } from "react";
import { useApp } from "../lib/contexto";
import { mesCurto, nomeDoMes } from "../lib/datas";
import { Gaveta } from "./Gaveta";
import { Icone } from "./Icone";

/** Mês, tema e olho: aparecem no topo de todas as telas. */
export function Acoes({ semMes = false }: { semMes?: boolean }) {
  const { mes, meses, setMes, oculto, alternarOculto, tema, alternarTema } = useApp();
  const [aberta, setAberta] = useState(false);
  return (
    <>
      <div className="acoes">
        <button type="button" className="round" onClick={alternarTema} aria-label={tema === "dark" ? "Usar tema claro" : "Usar tema escuro"}>
          <Icone nome={tema === "dark" ? "sol" : "lua"} />
        </button>
        <button type="button" className="round" onClick={alternarOculto} aria-pressed={oculto} aria-label={oculto ? "Mostrar valores" : "Esconder valores"}>
          <Icone nome={oculto ? "olhoFechado" : "olho"} />
        </button>
        {!semMes && mes && (
          <button type="button" className="mesbtn" onClick={() => setAberta(true)} aria-haspopup="dialog">
            {mesCurto(mes)} <Icone nome="baixo" tam={18} />
          </button>
        )}
      </div>
      <Gaveta aberta={aberta} titulo="Escolher mês" onFechar={() => setAberta(false)}>
        <h2 className="gtitulo">Mês</h2>
        {meses.map((m) => (
          <button key={m} type="button" className="mrow" aria-current={m === mes} onClick={() => { setMes(m); setAberta(false); }}>
            <span>{nomeDoMes(m)}</span><span>{m === mes ? "✓" : ""}</span>
          </button>
        ))}
      </Gaveta>
    </>
  );
}
