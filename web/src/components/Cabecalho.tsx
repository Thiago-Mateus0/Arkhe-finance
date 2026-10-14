import { hrefDe, type Rota } from "../lib/rotas";
import { Acoes } from "./Acoes";
import { Icone } from "./Icone";

/** Título da tela e as ações do topo. `voltar` mostra a seta para outra tela. */
export function Cabecalho({ titulo, voltar, semMes = false }: { titulo: string; voltar?: Rota; semMes?: boolean }) {
  return (
    <header className="cab">
      <div className="cab-esq">
        {voltar && <a className="round" href={hrefDe(voltar)} aria-label="Voltar"><Icone nome="voltar" /></a>}
        <h1>{titulo}</h1>
      </div>
      <Acoes semMes={semMes} />
    </header>
  );
}
