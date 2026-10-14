import { useState } from "react";
import { enviar, type Tx } from "../lib/api";
import { KIND, SEM_CATEGORIA } from "../lib/categorias";
import { useApp } from "../lib/contexto";
import { diaCurto } from "../lib/datas";
import { brl } from "../lib/money";
import { useApi } from "../lib/useApi";
import { Gaveta } from "./Gaveta";
import { nomeBonito } from "./LinhaTx";

/** Categorizar um lançamento, com a opção de lembrar o nome (cria regra). */
export function TxGaveta({ tx, onFechar }: { tx: Tx | null; onFechar: () => void }) {
  return (
    <Gaveta aberta={tx !== null} titulo="Categorizar lançamento" onFechar={onFechar}>
      {tx && <Conteudo key={tx.id} tx={tx} onFechar={onFechar} />}
    </Gaveta>
  );
}

function Conteudo({ tx, onFechar }: { tx: Tx; onFechar: () => void }) {
  const { invalidar } = useApp();
  const { estado } = useApi<string[]>("/categories");
  const [categoria, setCategoria] = useState(tx.category === SEM_CATEGORIA ? "" : tx.category);
  const [lembrar, setLembrar] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);
  const base = estado.fase === "ok" ? estado.dados : [];
  const sugestoes = [...new Set([...base, "Família", "Pessoas"])].filter((c) => c !== SEM_CATEGORIA).sort((a, b) => a.localeCompare(b, "pt-BR"));
  const entrada = tx.amount_cents > 0;

  const salvar = async () => {
    const c = categoria.trim();
    if (!c) { setErro("Escolha ou escreva uma categoria."); return; }
    setSalvando(true); setErro(null);
    try {
      await enviar(`/transactions/${tx.id}`, "PATCH", { category: c, remember: lembrar });
      invalidar(); onFechar();
    } catch (e) { setErro((e as Error).message); setSalvando(false); }
  };

  return (
    <>
      <h2 className="gtitulo">{nomeBonito(tx)}</h2>
      <div className={`val big n v ${entrada ? "pos" : ""}`}>{brl(Math.abs(tx.amount_cents))}</div>
      <p className="sub" style={{ whiteSpace: "normal" }}>{diaCurto(tx.date)} · {KIND[tx.kind] ?? tx.kind}</p>
      <p className="detalhe">{tx.description}</p>
      <label className="campo" htmlFor="cat">Categoria</label>
      <input id="cat" type="text" list="cats" value={categoria} onChange={(e) => setCategoria(e.target.value)} placeholder="Ex.: Transporte" autoComplete="off" autoFocus />
      <datalist id="cats">{sugestoes.map((c) => <option key={c} value={c} />)}</datalist>
      <div className="chips">
        {sugestoes.slice(0, 12).map((c) => (
          <button key={c} type="button" className="chip" aria-pressed={categoria === c} onClick={() => setCategoria(c)}>{c}</button>
        ))}
      </div>
      <label className="regra">
        <span>Lembrar para o mesmo nome<small>Cria uma regra para os próximos lançamentos</small></span>
        <span className="sw"><input type="checkbox" checked={lembrar} onChange={(e) => setLembrar(e.target.checked)} /><span /></span>
      </label>
      {erro && <p className="erro-campo" role="alert">{erro}</p>}
      <button type="button" className="btn" onClick={salvar} disabled={salvando}>Salvar</button>
    </>
  );
}
