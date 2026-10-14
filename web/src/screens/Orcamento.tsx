import { useEffect, useState } from "react";
import { Cabecalho } from "../components/Cabecalho";
import { Carregando, Erro } from "../components/Estados";
import { Gaveta } from "../components/Gaveta";
import { api, enviar, type Budgets, type ItemOrcamento } from "../lib/api";
import { corDaCategoria, SEM_CATEGORIA } from "../lib/categorias";
import { useApp } from "../lib/contexto";
import { brl, toCents } from "../lib/money";
import { useApi } from "../lib/useApi";
import { parseValor } from "../lib/valor";

const ESTADO = {
  ok: { rotulo: "Dentro do limite", icone: "✓", cor: "var(--pos)" },
  atencao: { rotulo: "Atenção", icone: "⚠", cor: "var(--warn)" },
  estourou: { rotulo: "Estourou", icone: "⛔", cor: "var(--neg)" },
} as const;

export function Orcamento() {
  const { mes } = useApp();
  const { estado, recarregar } = useApi<Budgets>(mes ? `/budgets?month=${mes}` : null);
  const [edit, setEdit] = useState<{ categoria: string; limite: number | null } | null>(null);

  return (
    <>
      <Cabecalho titulo="Orçamento" />
      {estado.fase === "carregando" && <Carregando />}
      {estado.fase === "erro" && <Erro msg={estado.msg} onTentar={recarregar} />}
      {estado.fase === "ok" && <Corpo b={estado.dados} onEditar={setEdit} />}
      <Gaveta aberta={edit !== null} titulo="Orçamento" onFechar={() => setEdit(null)}>
        {edit && <Editor key={edit.categoria} inicial={edit} onFechar={() => setEdit(null)} />}
      </Gaveta>
    </>
  );
}

function Corpo({ b, onEditar }: { b: Budgets; onEditar: (e: { categoria: string; limite: number | null }) => void }) {
  const por = { estourou: 0, atencao: 0, ok: 0 };
  b.itens.forEach((i) => { por[i.estado] += 1; });
  const resumo = por.estourou || por.atencao
    ? [por.estourou ? `${por.estourou} estourou` : "", por.atencao ? `${por.atencao} em atenção` : ""].filter(Boolean).join(" · ")
    : "Tudo dentro do limite";
  return (
    <>
      {b.itens.length > 0 && (
        <div className="card tint-c">
          <div className="lbl">Orçado no mês</div>
          <div className="val big n v">{brl(toCents(b.orcado_total))}</div>
          <p className="sub n v">Gasto nessas categorias: {brl(toCents(b.gasto_nas_categorias))}</p>
          <p className="sub" style={{ whiteSpace: "normal" }}>{resumo}</p>
        </div>
      )}
      {b.itens.map((i, k) => <Item key={i.categoria} i={i} k={k} onEditar={onEditar} />)}
      {b.itens.length === 0 && <p className="empty">Nenhum orçamento ainda.<br />Escolha uma categoria e um limite mensal.</p>}
      <button type="button" className="btn" onClick={() => onEditar({ categoria: "", limite: null })}>Novo orçamento</button>
      <p className="nota">O limite vale todos os meses. Atenção a partir de 80%; estourou quando passa do limite. Só conta gasto: repasse, transferência e pagamento de fatura ficam de fora.</p>
    </>
  );
}

function Item({ i, k, onEditar }: { i: ItemOrcamento; k: number; onEditar: (e: { categoria: string; limite: number | null }) => void }) {
  const e = ESTADO[i.estado];
  return (
    <button type="button" className="card orc rise" style={{ ["--i" as string]: k }} onClick={() => onEditar({ categoria: i.categoria, limite: toCents(i.limite) })}>
      <div className="orc-topo">
        <span className="ic" style={{ ["--cc" as string]: corDaCategoria(i.categoria) }}>{i.categoria.slice(0, 2).toUpperCase()}</span>
        <b>{i.categoria}</b>
        <span className="estado" style={{ color: e.cor }}>{e.icone} {e.rotulo}</span>
      </div>
      <div className="track" role="img" aria-label={`${Math.round(i.percentual)}% do limite`}>
        <div className="fill" style={{ width: `${Math.min(100, i.percentual)}%`, background: e.cor }} />
      </div>
      <div className="meta">
        <span className="n v">{brl(toCents(i.gasto))} de {brl(toCents(i.limite))}</span>
        <span className="n v">{i.restante < 0 ? `passou ${brl(toCents(-i.restante))}` : `restam ${brl(toCents(i.restante))}`}</span>
      </div>
    </button>
  );
}

function Editor({ inicial, onFechar }: { inicial: { categoria: string; limite: number | null }; onFechar: () => void }) {
  const { invalidar } = useApp();
  const novo = !inicial.categoria;
  const [categoria, setCategoria] = useState(inicial.categoria);
  const [limite, setLimite] = useState(inicial.limite ? (inicial.limite / 100).toFixed(2).replace(".", ",") : "");
  const [cats, setCats] = useState<string[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [confirmar, setConfirmar] = useState(false);

  useEffect(() => { api<string[]>("/categories").then((c) => setCats(c.filter((x) => x !== SEM_CATEGORIA))).catch(() => undefined); }, []);

  const salvar = async () => {
    const c = categoria.trim(), v = parseValor(limite);
    if (!c) { setErro("Escolha uma categoria."); return; }
    if (v === null) { setErro("Informe um limite maior que zero, como 150 ou 150,50."); return; }
    try {
      await enviar(`/budgets/${encodeURIComponent(c)}`, "PUT", { limite: v / 100 });
      invalidar(); onFechar();
    } catch (e) { setErro((e as Error).message); }
  };
  const remover = async () => {
    try { await enviar(`/budgets/${encodeURIComponent(inicial.categoria)}`, "DELETE"); invalidar(); onFechar(); }
    catch (e) { setErro((e as Error).message); }
  };

  return (
    <>
      <h2 className="gtitulo">{novo ? "Novo orçamento" : "Editar orçamento"}</h2>
      <label className="campo" htmlFor="bcat">Categoria</label>
      <input id="bcat" type="text" list="blist" value={categoria} onChange={(e) => setCategoria(e.target.value)} placeholder="Ex.: Delivery" autoComplete="off" readOnly={!novo} autoFocus={novo} />
      <datalist id="blist">{cats.map((c) => <option key={c} value={c} />)}</datalist>
      <label className="campo" htmlFor="blim">Limite por mês (R$)</label>
      <input id="blim" type="text" inputMode="decimal" value={limite} onChange={(e) => setLimite(e.target.value)} placeholder="Ex.: 150,00" autoComplete="off" autoFocus={!novo} />
      {erro && <p className="erro-campo" role="alert">{erro}</p>}
      <button type="button" className="btn" onClick={salvar}>Salvar</button>
      {!novo && !confirmar && <button type="button" className="chip perigo" onClick={() => setConfirmar(true)}>Remover orçamento</button>}
      {!novo && confirmar && (
        <div className="confirma" role="alert">
          <p>Remover o orçamento de {inicial.categoria}? Os lançamentos continuam.</p>
          <button type="button" className="chip perigo" onClick={remover}>Sim, remover</button>
          <button type="button" className="chip" onClick={() => setConfirmar(false)}>Cancelar</button>
        </div>
      )}
    </>
  );
}
