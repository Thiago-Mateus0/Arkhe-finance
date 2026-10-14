import { Menu } from "./components/Menu";
import { Provedor, useApp } from "./lib/contexto";
import { Atividades } from "./screens/Atividades";
import { Fluxo } from "./screens/Fluxo";
import { Gastos } from "./screens/Gastos";
import { Importar } from "./screens/Importar";
import { Inicio } from "./screens/Inicio";
import { Orcamento } from "./screens/Orcamento";
import { Regras } from "./screens/Regras";

function Tela() {
  const { local } = useApp();
  switch (local.rota) {
    case "atividades": return <Atividades />;
    case "gastos": return <Gastos />;
    case "orcamento": return <Orcamento />;
    case "fluxo": return <Fluxo />;
    case "regras": return <Regras />;
    case "importar": return <Importar />;
    default: return <Inicio />;
  }
}

function Casca() {
  const { oculto, local } = useApp();
  return (
    <div className={`app${oculto ? " hide" : ""}`}>
      <Menu />
      <main className="page" key={local.rota}>
        <Tela />
      </main>
    </div>
  );
}

export function App() {
  return <Provedor><Casca /></Provedor>;
}
