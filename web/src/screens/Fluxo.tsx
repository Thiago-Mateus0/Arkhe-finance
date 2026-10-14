import { useState } from "react";
import { Cabecalho } from "../components/Cabecalho";
import { Carregando, Erro, Vazio } from "../components/Estados";
import { LinhaTx } from "../components/LinhaTx";
import type { Daily, Monthly, Tx } from "../lib/api";
import { useApp } from "../lib/contexto";
import { soMes } from "../lib/datas";
import { brl, toCents } from "../lib/money";
import { useApi } from "../lib/useApi";

type Modo = "geral" | "entradas" | "saidas";
const MODOS: { k: Modo; r: string }[] = [{ k: "geral", r: "Geral" }, { k: "entradas", r: "Entradas" }, { k: "saidas", r: "Saídas" }];

export function Fluxo() {
  const { mes } = useApp();
  const [modo, setModo] = useState<Modo>("geral");
  const rep = useApi<Monthly>(mes ? `/reports/monthly?month=${mes}` : null);
  const dia = useApi<Daily>(mes ? `/reports/daily?month=${mes}` : null);
  const txs = useApi<Tx[]>(mes ? `/transactions?month=${mes}&kinds=income,expense&desc=true` : null);

  if (!mes) return <><Cabecalho titulo="Fluxo" /><Vazio>Nada importado ainda.</Vazio></>;
  for (const x of [rep, dia, txs]) {
    if (x.estado.fase === "erro") return <><Cabecalho titulo="Fluxo" /><Erro msg={x.estado.msg} onTentar={x.recarregar} /></>;
  }
  if (rep.estado.fase !== "ok" || dia.estado.fase !== "ok" || txs.estado.fase !== "ok") return <><Cabecalho titulo="Fluxo" /><Carregando /></>;

  const r = rep.estado.dados, d = dia.estado.dados, tx = txs.estado.dados;
  const entradas = toCents(r.receitas_total), gastos = toCents(r.gastos_total), saldo = entradas - gastos;
  const BW = 34, W = BW * d.dias.length + 20, H = 190, base = H - 22;
  const valor = (x: { entradas: number; gastos: number }) =>
    modo === "entradas" ? x.entradas : modo === "saidas" ? x.gastos : Math.max(x.entradas, x.gastos);
  const max = Math.max(1, ...d.dias.map(valor));
  const h = (v: number) => (v / max) * (base - 14);

  const barra = (cx: number, v: number, cor: string, rotulo: string, dia: number) =>
    v > 0
      ? <rect key={`${cx}-${rotulo}`} x={cx} y={base - h(v)} width="10" height={h(v)} rx="5" fill={cor}><title>{dia}: {rotulo} {brl(toCents(v))}</title></rect>
      : <circle key={`${cx}-${rotulo}`} cx={cx + 5} cy={base - 5} r="4" fill="none" stroke="var(--edge-2)" strokeDasharray="2 2" />;

  return (
    <>
      <Cabecalho titulo="Fluxo" />
      <div className="chips" role="group" aria-label="Tipo">
        {MODOS.map((m) => <button key={m.k} type="button" className="chip" aria-pressed={modo === m.k} onClick={() => setModo(m.k)}>{m.r}</button>)}
      </div>
      <p className="lbl">Fluxo geral em {soMes(mes)}</p>
      <div className={`val big n v ${saldo >= 0 ? "pos" : "neg"}`} style={{ fontSize: "2.6rem" }}>{brl(saldo, true)}</div>
      <p className="t2"><span className="pos">●</span> Entradas <span className="n v">{brl(entradas)}</span><br /><span className="neg">●</span> Gastos <span className="n v">{brl(gastos)}</span></p>
      <p className="nota">Não conta Pix de ida e volta, transferências entre suas contas nem pagamento de fatura.</p>

      <div className="card rolax">
        <svg viewBox={`0 0 ${W} ${H}`} width={W} role="img" aria-label="Entradas e gastos por dia" style={{ display: "block", minWidth: "100%" }}>
          <line x1="0" x2={W} y1={base} y2={base} stroke="var(--edge-2)" />
          {d.dias.map((x, i) => {
            const cx = 12 + i * BW;
            return (
              <g key={x.dia}>
                {modo === "geral"
                  ? <>{barra(cx, x.entradas, "var(--pos)", "entradas", x.dia)}{barra(cx + 14, x.gastos, "var(--neg)", "gastos", x.dia)}</>
                  : barra(cx + 7, modo === "entradas" ? x.entradas : x.gastos, modo === "entradas" ? "var(--pos)" : "var(--neg)", modo === "entradas" ? "entradas" : "gastos", x.dia)}
                <text x={cx + 12} y={H - 4} textAnchor="middle" fill="var(--muted)" fontSize="10">{String(x.dia).padStart(2, "0")}</text>
              </g>
            );
          })}
        </svg>
      </div>

      <h2 className="sec">Últimos lançamentos</h2>
      <div className="card lista">
        {tx.slice(0, 6).map((t) => <LinhaTx key={t.id} t={t} />)}
        {tx.length === 0 && <p className="empty">Sem lançamentos.</p>}
      </div>
    </>
  );
}
