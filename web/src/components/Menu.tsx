import { useApp } from "../lib/contexto";
import { sair } from "../lib/sessao";
import { NUVEM } from "../lib/supabase";
import { hrefDe, type Rota } from "../lib/rotas";
import { Icone, type NomeIcone } from "./Icone";
import { Marca } from "./Marca";

const ITENS: { rota: Rota; rotulo: string; icone: NomeIcone }[] = [
  { rota: "inicio", rotulo: "Início", icone: "casa" },
  { rota: "atividades", rotulo: "Atividades", icone: "lista" },
  { rota: "gastos", rotulo: "Gastos", icone: "pizza" },
  { rota: "orcamento", rotulo: "Orçamento", icone: "alvo" },
  { rota: "fluxo", rotulo: "Fluxo", icone: "fluxo" },
];

/** Celular: pílula flutuante + botão de importar. Computador (900 px ou mais): menu lateral. */
export function Menu() {
  const { local } = useApp();
  const ativa = local.rota === "regras" ? "atividades" : local.rota;
  return (
    <>
      <aside className="lateral" aria-label="Menu">
        <div className="marca"><Marca /><b>Arkhe Finance</b></div>
        <nav>
          {ITENS.map((i) => (
            <a key={i.rota} href={hrefDe(i.rota)} aria-current={ativa === i.rota ? "page" : undefined}><Icone nome={i.icone} /> {i.rotulo}</a>
          ))}
          <a href={hrefDe("importar")} aria-current={ativa === "importar" ? "page" : undefined}><Icone nome="enviar" /> Importar</a>
          {NUVEM && <button type="button" className="btn" onClick={sair}>Sair</button>}
        </nav>
      </aside>

      <div className="dock">
        {local.rota === "inicio" && (
          <a className="ask glass" href={hrefDe("importar")}><Icone nome="enviar" />Importar extrato ou fatura (CSV)</a>
        )}
        <div className="navrow">
          <nav className="nav glass" aria-label="Navegação">
            {ITENS.map((i) => (
              <a key={i.rota} href={hrefDe(i.rota)} aria-label={i.rotulo} aria-current={ativa === i.rota ? "page" : undefined}><Icone nome={i.icone} tam={24} /></a>
            ))}
          </nav>
          <a className="plus" href={hrefDe("importar")} aria-label="Importar CSV"><Icone nome="mais" tam={28} /></a>
        </div>
      </div>
    </>
  );
}
