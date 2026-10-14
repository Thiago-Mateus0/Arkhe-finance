import { useEffect, useState } from "react";
import { Cabecalho } from "../components/Cabecalho";
import { Carregando, Erro } from "../components/Estados";
import { Gaveta } from "../components/Gaveta";
import { api, enviar, type Regra } from "../lib/api";
import { corDaCategoria, SEM_CATEGORIA } from "../lib/categorias";
import { useApp } from "../lib/contexto";
import { useApi } from "../lib/useApi";

export function Regras() {
  const { estado, recarregar } = useApi<Regra[]>("/rules");
  const [edit, setEdit] = useState<Regra | "nova" | null>(null);
  const ord = estado.fase === "ok"
    ? [...estado.dados].sort((a, b) => a.category.localeCompare(b.category, "pt-BR") || a.pattern.localeCompare(b.pattern, "pt-BR"))
    : [];
  return (
    <>
      <Cabecalho titulo="Regras de categoria" voltar="atividades" semMes />
      <p className="nota">Se o nome do lançamento contém o texto, ele entra na categoria. Em caso de várias regras, vence a de maior prioridade; empatando, a mais específica. Categoria escolhida à mão em um lançamento nunca é alterada por regra.</p>
      <button type="button" className="btn" onClick={() => setEdit("nova")}>Nova regra</button>
      {estado.fase === "carregando" && <Carregando />}
      {estado.fase === "erro" && <Erro msg={estado.msg} onTentar={recarregar} />}
      {estado.fase === "ok" && ord.length === 0 && <p className="empty">Nenhuma regra ainda.</p>}
      {ord.length > 0 && (
        <div className="card lista">
          {ord.map((r) => (
            <button key={r.id} type="button" className="tx" onClick={() => setEdit(r)}>
              <div className="ic" style={{ ["--cc" as string]: corDaCategoria(r.category) }}>{r.category.slice(0, 2).toUpperCase()}</div>
              <div className="t"><b>{r.pattern}</b><small>vira {r.category}</small></div>
              {r.priority !== 0 && <span className="sub">prioridade {r.priority}</span>}
            </button>
          ))}
        </div>
      )}
      <Gaveta aberta={edit !== null} titulo="Regra de categoria" onFechar={() => setEdit(null)}>
        {edit && <Editor key={edit === "nova" ? "nova" : edit.id} regra={edit === "nova" ? null : edit} onFechar={() => setEdit(null)} />}
      </Gaveta>
    </>
  );
}

function Editor({ regra, onFechar }: { regra: Regra | null; onFechar: () => void }) {
  const { invalidar } = useApp();
  const [pattern, setPattern] = useState(regra?.pattern ?? "");
  const [category, setCategory] = useState(regra?.category ?? "");
  const [prioridade, setPrioridade] = useState(String(regra?.priority ?? 0));
  const [cats, setCats] = useState<string[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [confirmar, setConfirmar] = useState(false);

  useEffect(() => { api<string[]>("/categories").then((c) => setCats(c.filter((x) => x !== SEM_CATEGORIA))).catch(() => undefined); }, []);

  const salvar = async () => {
    const p = pattern.trim(), c = category.trim(), pri = Number.parseInt(prioridade, 10);
    if (!p) { setErro("Escreva o texto que a regra procura."); return; }
    if (!c) { setErro("Escolha uma categoria."); return; }
    if (Number.isNaN(pri)) { setErro("Prioridade precisa ser um número inteiro."); return; }
    try {
      await enviar(regra ? `/rules/${regra.id}` : "/rules", regra ? "PUT" : "POST", { pattern: p, category: c, priority: pri });
      invalidar(); onFechar();
    } catch (e) { setErro((e as Error).message); }
  };
  const apagar = async () => {
    if (!regra) return;
    try { await enviar(`/rules/${regra.id}`, "DELETE"); invalidar(); onFechar(); }
    catch (e) { setErro((e as Error).message); }
  };

  return (
    <>
      <h2 className="gtitulo">{regra ? "Editar regra" : "Nova regra"}</h2>
      <label className="campo" htmlFor="rpat">Quando o nome contém</label>
      <input id="rpat" type="text" value={pattern} onChange={(e) => setPattern(e.target.value)} placeholder="Ex.: ifood" autoComplete="off" autoFocus />
      <label className="campo" htmlFor="rcat">Categoria</label>
      <input id="rcat" type="text" list="rlist" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="Ex.: Delivery" autoComplete="off" />
      <datalist id="rlist">{cats.map((c) => <option key={c} value={c} />)}</datalist>
      <label className="campo" htmlFor="rpri">Prioridade (maior vence; padrão 0)</label>
      <input id="rpri" type="number" inputMode="numeric" step="1" value={prioridade} onChange={(e) => setPrioridade(e.target.value)} />
      {erro && <p className="erro-campo" role="alert">{erro}</p>}
      <button type="button" className="btn" onClick={salvar}>Salvar</button>
      {regra && !confirmar && <button type="button" className="chip perigo" onClick={() => setConfirmar(true)}>Apagar regra</button>}
      {regra && confirmar && (
        <div className="confirma" role="alert">
          <p>Apagar esta regra? Os lançamentos voltam a ser categorizados pelas outras regras; os que você categorizou à mão não mudam.</p>
          <button type="button" className="chip perigo" onClick={apagar}>Sim, apagar</button>
          <button type="button" className="chip" onClick={() => setConfirmar(false)}>Cancelar</button>
        </div>
      )}
    </>
  );
}
