import { useMemo, useState } from "react";
import { Cabecalho } from "../components/Cabecalho";
import { Carregando, Erro, Vazio } from "../components/Estados";
import type { Daily, Monthly } from "../lib/api";
import { corDaCategoria, SEM_CATEGORIA, temCorPropria } from "../lib/categorias";
import { useApp } from "../lib/contexto";
import { mesAtual, soMes } from "../lib/datas";
import { acumulado, suave } from "../lib/grafico";
import { brl, toCents } from "../lib/money";
import { useApi } from "../lib/useApi";

const W = 340, H = 190, PAD = 8;

export function Gastos() {
  const { mes, ir } = useApp();
  const rep = useApi<Monthly>(mes ? `/reports/monthly?month=${mes}` : null);
  const dia = useApi<Daily>(mes ? `/reports/daily?month=${mes}` : null);
  if (!mes) return <><Cabecalho titulo="Gastos" /><Vazio>Nada importado ainda.</Vazio></>;
  if (rep.estado.fase === "erro") return <><Cabecalho titulo="Gastos" /><Erro msg={rep.estado.msg} onTentar={rep.recarregar} /></>;
  if (dia.estado.fase === "erro") return <><Cabecalho titulo="Gastos" /><Erro msg={dia.estado.msg} onTentar={dia.recarregar} /></>;
  if (rep.estado.fase !== "ok" || dia.estado.fase !== "ok") return <><Cabecalho titulo="Gastos" /><Carregando /></>;
  return <Conteudo mes={mes} rep={rep.estado.dados} daily={dia.estado.dados} ir={ir} />;
}

function Conteudo({ mes, rep, daily, ir }: { mes: string; rep: Monthly; daily: Daily; ir: (r: "atividades", p?: Record<string, string | undefined>) => void }) {
  const n = daily.anterior.length || daily.dias.length;
  const upto = mes === mesAtual() ? Math.min(new Date().getDate(), n) : n;
  const cur = useMemo(() => acumulado(daily.dias.map((d) => toCents(d.gastos)), n), [daily, n]);
  const prev = useMemo(() => acumulado(daily.anterior.map((d) => toCents(d.gastos)), n), [daily, n]);
  const total = toCents(rep.gastos_total);
  const aqui = cur[upto - 1] ?? 0, antes = prev[upto - 1] ?? 0;
  const delta = antes ? ((aqui - antes) / antes) * 100 : null;
  const [sel, setSel] = useState<number | null>(null);

  const max = Math.max(1, ...cur.slice(0, upto), ...prev) * 1.08;
  const X = (i: number) => PAD + (i / Math.max(1, n - 1)) * (W - 2 * PAD);
  const Y = (v: number) => H - PAD - (v / max) * (H - 2 * PAD);
  const ptsCur = cur.slice(0, upto).map((v, i) => [X(i), Y(v)] as const);
  const ptsPrev = prev.map((v, i) => [X(i), Y(v)] as const);
  const linha = suave(ptsCur);
  const ultimo = ptsCur[ptsCur.length - 1];
  const i = sel ?? upto - 1;

  const cats = rep.por_categoria.map((c) => ({ nome: c.categoria, cents: toCents(c.valor), qtd: c.qtd }));
  const proprias = cats.filter((c) => temCorPropria(c.nome)).slice(0, 6);
  const pend = cats.find((c) => c.nome === SEM_CATEGORIA);
  const outras = cats.filter((c) => c !== pend && !proprias.includes(c)).reduce((s, c) => s + c.cents, 0);
  const fatias = [
    ...proprias.map((c) => ({ nome: c.nome, cents: c.cents, cor: corDaCategoria(c.nome) })),
    ...(pend ? [{ nome: SEM_CATEGORIA, cents: pend.cents, cor: "var(--c0)" }] : []),
    ...(outras > 0 ? [{ nome: "Outras categorias", cents: outras, cor: "var(--other)" }] : []),
  ];

  return (
    <>
      <Cabecalho titulo="Gastos" />
      <p className="lbl">Gastos em {soMes(mes)}</p>
      <div className="val big n v" style={{ fontSize: "2.6rem" }}>{brl(total)}</div>
      {delta === null
        ? <p className="sub">Sem mês anterior para comparar</p>
        : <p className="delta"><span className={delta <= 0 ? "pos" : "neg"}>{delta <= 0 ? "↓" : "↑"} {Math.abs(delta).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%</span>{" "}
            <span className="t2">vs <span className="n v">{brl(antes)}</span> no mesmo ponto do mês anterior</span></p>}

      <div className="legenda"><span><i />Este mês</span><span><i className="trac" />Mês anterior</span></div>
      <div className="card tint-c">
        <div className="chartwrap"
          onPointerDown={(e) => { e.currentTarget.setPointerCapture(e.pointerId); mover(e); }}
          onPointerMove={(e) => { if (e.buttons > 0 || e.pointerType === "mouse") mover(e); }}
          onPointerUp={() => setSel(null)} onPointerLeave={() => setSel(null)} onPointerCancel={() => setSel(null)}>
          <div className={`bubble v${sel === null ? "" : " on"}`} style={{ left: `${Math.max(22, Math.min(78, (X(i) / W) * 100))}%` }}>
            Dia {i + 1} · {brl(cur[i] ?? 0)}<br /><span className="mut">mês anterior: {brl(prev[i] ?? 0)}</span>
          </div>
          <svg className="chart" viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={`Gasto acumulado no mês: ${brl(aqui)}`}>
            <defs>
              <linearGradient id="gg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--accent)" stopOpacity=".35" /><stop offset="1" stopColor="var(--accent)" stopOpacity="0" /></linearGradient>
            </defs>
            <line x1={PAD} x2={W - PAD} y1={H - PAD} y2={H - PAD} stroke="var(--edge-2)" />
            <path d={suave(ptsPrev)} fill="none" stroke="var(--muted)" strokeWidth="2" strokeDasharray="5 5" strokeLinecap="round" />
            {ptsCur.length > 1 && ultimo && <path className="areafade" d={`${linha} L${ultimo[0]} ${H - PAD} L${ptsCur[0]![0]} ${H - PAD} Z`} fill="url(#gg)" />}
            <path className="draw" pathLength={1} d={linha} fill="none" stroke="var(--accent)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
            {sel !== null && <line x1={X(i)} x2={X(i)} y1={PAD} y2={H - PAD} stroke="var(--edge-2)" strokeDasharray="3 3" />}
            <circle cx={X(i)} cy={Y(cur[i] ?? 0)} r="5" fill="var(--accent)" stroke="var(--card)" strokeWidth="2" />
          </svg>
        </div>
        <div className="axis"><span>01</span><span>{String(Math.ceil(n / 2)).padStart(2, "0")}</span><span>{String(n).padStart(2, "0")}</span></div>
      </div>

      <details className="card detalhes">
        <summary>Ver valores por dia</summary>
        <table>
          <thead><tr><th>Dia</th><th>Gasto</th></tr></thead>
          <tbody>
            {daily.dias.filter((d) => d.gastos > 0).map((d) => <tr key={d.dia}><td>{d.dia}</td><td className="n v">{brl(toCents(d.gastos))}</td></tr>)}
            {daily.dias.every((d) => d.gastos === 0) && <tr><td colSpan={2}>Sem gastos</td></tr>}
          </tbody>
        </table>
      </details>

      <h2 className="sec">Categorias</h2>
      {total > 0 && (
        <div className="card rosca">
          <Rosca fatias={fatias} total={total} />
        </div>
      )}
      <div className="card lista">
        {cats.length === 0 && <p className="empty">Sem gastos neste mês.</p>}
        {cats.map((c) => (
          <button key={c.nome} type="button" className="tx" onClick={() => ir("atividades", { cat: c.nome })}>
            <div className="ic" style={{ ["--cc" as string]: corDaCategoria(c.nome) }}>{c.nome.slice(0, 2).toUpperCase()}</div>
            <div className="t"><b>{c.nome}</b><small>{total ? Math.round((c.cents / total) * 1000) / 10 : 0}% · {c.qtd} {c.qtd === 1 ? "transação" : "transações"}</small></div>
            <span className="n v">{brl(c.cents)}</span>
          </button>
        ))}
      </div>
    </>
  );

  function mover(e: React.PointerEvent<HTMLDivElement>) {
    const r = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width) * W;
    setSel(Math.max(0, Math.min(upto - 1, Math.round(((x - PAD) / (W - 2 * PAD)) * (n - 1)))));
  }
}

function Rosca({ fatias, total }: { fatias: { nome: string; cents: number; cor: string }[]; total: number }) {
  const R = 90, C = 2 * Math.PI * R, SW = 18, GAP = 4;
  let acc = 0;
  return (
    <svg className="donut" viewBox="0 0 220 220" role="img" aria-label="Gastos por categoria">
      <circle cx="110" cy="110" r={R} fill="none" stroke="var(--edge)" strokeWidth={SW} />
      {fatias.map((f) => {
        const frac = total ? f.cents / total : 0;
        const len = Math.max(0.01, frac * C - SW - GAP);
        const off = -(acc * C + SW / 2 + GAP / 2);
        acc += frac;
        return (
          <circle key={f.nome} cx="110" cy="110" r={R} fill="none" stroke={f.cor} strokeWidth={SW} strokeLinecap="round"
            strokeDasharray={`${len} ${C}`} strokeDashoffset={off} transform="rotate(-90 110 110)">
            <title>{f.nome}: {brl(f.cents)}</title>
          </circle>
        );
      })}
      <text x="110" y="108" textAnchor="middle" fill="var(--text)" fontSize="21" fontWeight="800" className="v">{brl(total)}</text>
      <text x="110" y="132" textAnchor="middle" fill="var(--muted)" fontSize="12">gastos no mês</text>
    </svg>
  );
}
