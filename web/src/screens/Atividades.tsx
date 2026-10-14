import { useEffect, useMemo, useState } from "react";
import { Cabecalho } from "../components/Cabecalho";
import { Carregando, Erro, Vazio } from "../components/Estados";
import { Icone } from "../components/Icone";
import { LinhaTx } from "../components/LinhaTx";
import { TxGaveta } from "../components/TxGaveta";
import type { Tx } from "../lib/api";
import { useApp } from "../lib/contexto";
import { rotuloDoDia } from "../lib/datas";
import { hrefDe } from "../lib/rotas";
import { SEM_CATEGORIA } from "../lib/categorias";
import { useApi } from "../lib/useApi";

const FILTROS = [
  { k: "all", r: "Todas" }, { k: "in", r: "Entradas" }, { k: "out", r: "Saídas" },
  { k: "uncat", r: "Sem categoria" }, { k: "card", r: "Cartão" }, { k: "hidden", r: "Não contam" },
] as const;

export function Atividades() {
  const { mes, local, ir } = useApp();
  const f = local.params.get("f") ?? "all";
  const cat = local.params.get("cat");
  const [q, setQ] = useState("");
  const [qAplicada, setQAplicada] = useState("");
  const [aberta, setAberta] = useState<Tx | null>(null);

  useEffect(() => { const t = setTimeout(() => setQAplicada(q), 250); return () => clearTimeout(t); }, [q]);

  const url = useMemo(() => {
    if (!mes) return null;
    const p = new URLSearchParams({ month: mes, desc: "true" });
    if (qAplicada.trim()) p.set("q", qAplicada.trim());
    if (cat) { p.set("kinds", "expense,income"); p.set("category", cat); }
    else if (f === "in") p.set("kind", "income");
    else if (f === "out") p.set("kind", "expense");
    else if (f === "uncat") { p.set("kind", "expense"); p.set("category", SEM_CATEGORIA); }
    else if (f === "hidden") p.set("kinds", "passthrough,transfer,card_payment,credit_funding,investment");
    else p.set("kinds", "income,expense");
    return `/transactions?${p}`;
  }, [mes, qAplicada, cat, f]);

  const { estado, recarregar } = useApi<Tx[]>(url);
  const grupos = useMemo(() => {
    if (estado.fase !== "ok") return [];
    const lista = f === "card" && !cat ? estado.dados.filter((t) => t.account === "nubank_fatura") : estado.dados;
    const out: { data: string; itens: Tx[] }[] = [];
    lista.forEach((t) => {
      const g = out[out.length - 1];
      if (g && g.data === t.date) g.itens.push(t); else out.push({ data: t.date, itens: [t] });
    });
    return out;
  }, [estado, f, cat]);

  return (
    <>
      <Cabecalho titulo="Atividades" />
      <a className="chip chip-link" href={hrefDe("regras")}><Icone nome="regras" tam={16} /> Regras de categoria</a>
      <label className="busca glass" htmlFor="q">
        <Icone nome="busca" />
        <input id="q" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar" aria-label="Buscar lançamentos" autoComplete="off" />
      </label>
      <div className="chips" role="group" aria-label="Filtros">
        {FILTROS.map((x) => (
          <button key={x.k} type="button" className="chip" aria-pressed={!cat && f === x.k}
            onClick={() => ir("atividades", { f: x.k === "all" ? undefined : x.k })}>{x.r}</button>
        ))}
      </div>
      {cat && <button type="button" className="chip" aria-pressed="true" onClick={() => ir("atividades")}>{cat} ✕</button>}

      {estado.fase === "carregando" && <Carregando />}
      {estado.fase === "erro" && <Erro msg={estado.msg} onTentar={recarregar} />}
      {estado.fase === "ok" && grupos.length === 0 && <Vazio>Nada por aqui.</Vazio>}
      {grupos.map((g) => (
        <section key={g.data}>
          <div className="dia">{rotuloDoDia(g.data)}</div>
          <div className="card lista">{g.itens.map((t) => <LinhaTx key={t.id} t={t} onAbrir={setAberta} comData={false} />)}</div>
        </section>
      ))}
      <TxGaveta tx={aberta} onFechar={() => setAberta(null)} />
    </>
  );
}
