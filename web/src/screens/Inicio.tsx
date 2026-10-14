import { useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import { Acoes } from "../components/Acoes";
import { Carregando, Erro } from "../components/Estados";
import { LinhaTx } from "../components/LinhaTx";
import type { Assinaturas, Budgets, Daily, Monthly, Parcelas, Tx } from "../lib/api";
import { corDaCategoria, SEM_CATEGORIA } from "../lib/categorias";
import { useApp } from "../lib/contexto";
import { mesAtual, nomeDoMes, saudacao } from "../lib/datas";
import { suave } from "../lib/grafico";
import { brl, toCents } from "../lib/money";
import { hrefDe } from "../lib/rotas";
import { useApi } from "../lib/useApi";

export interface Dados {
  rep: Monthly; daily: Daily; bud: Budgets; parc: Parcelas; ass: Assinaturas; tx: Tx[];
}

const Svg = ({ d, className = "ico" }: { d: string; className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" aria-hidden="true"><path d={d} /></svg>
);
const D = {
  repetir: "M17 2l4 4-4 4M3 11V9a3 3 0 013-3h15M7 22l-4-4 4-4M21 13v2a3 3 0 01-3 3H3",
  parcelas: "M4 7h16M4 12h10M4 17h6",
};

export function Inicio() {
  const { mes, meses, erroMeses, recarregarMeses } = useApp();
  const [aba, setAba] = useState<"contas" | "cartao">("contas");
  const q = mes ? `month=${mes}` : null;
  const rep = useApi<Monthly>(q && `/reports/monthly?${q}`);
  const daily = useApi<Daily>(q && `/reports/daily?${q}`);
  const bud = useApi<Budgets>(q && `/budgets?${q}`);
  const parc = useApi<Parcelas>(q && "/reports/parcelas");
  const ass = useApi<Assinaturas>(q && `/reports/assinaturas?${q}`);
  const tx = useApi<Tx[]>(q && `/transactions?${q}&kinds=income,expense&desc=true`);
  const todos = [rep, daily, bud, parc, ass, tx];
  const falha = todos.find((x) => x.estado.fase === "erro");
  const pronto = rep.estado.fase === "ok" && daily.estado.fase === "ok" && bud.estado.fase === "ok" &&
    parc.estado.fase === "ok" && ass.estado.fase === "ok" && tx.estado.fase === "ok";
  const dados: Dados | null = pronto ? {
    rep: (rep.estado as { dados: Monthly }).dados, daily: (daily.estado as { dados: Daily }).dados,
    bud: (bud.estado as { dados: Budgets }).dados, parc: (parc.estado as { dados: Parcelas }).dados,
    ass: (ass.estado as { dados: Assinaturas }).dados, tx: (tx.estado as { dados: Tx[] }).dados,
  } : null;

  return (
    <>
      <div className="aurora" aria-hidden="true"><i /><i /><i /><i /></div>
      <header className="cab cab-inicio">
        <svg viewBox="0 0 32 32" width="46" height="46" aria-label="Arkhe Finance" role="img" className="so-celular">
          <rect width="32" height="32" rx="9" fill="var(--accent)" />
          <rect x="7" y="17" width="4.5" height="8" rx="2.25" fill="var(--on-accent)" />
          <rect x="13.75" y="12" width="4.5" height="13" rx="2.25" fill="var(--on-accent)" />
          <rect x="20.5" y="7" width="4.5" height="18" rx="2.25" fill="var(--on-accent)" />
        </svg>
        <Acoes />
      </header>
      <h1 className="hello">{saudacao()}</h1>
      <div className="tabs" role="tablist" aria-label="Visão">
        <button type="button" role="tab" className="tab" aria-selected={aba === "contas"} onClick={() => setAba("contas")}>Contas</button>
        <button type="button" role="tab" className="tab" aria-selected={aba === "cartao"} onClick={() => setAba("cartao")}>Cartão</button>
      </div>

      {erroMeses && <Erro msg={erroMeses} onTentar={recarregarMeses} />}
      {!erroMeses && meses.length === 0 && <p className="empty">Nada importado ainda. <a href={hrefDe("importar")} style={{ color: "var(--accent)" }}>Importe um extrato</a> para começar.</p>}
      {!falha && !pronto && mes && <Carregando />}
      {falha && falha.estado.fase === "erro" && <Erro msg={falha.estado.msg} onTentar={() => todos.forEach((x) => x.recarregar())} />}
      {dados && (aba === "contas" ? <Contas d={dados} mes={mes!} /> : <Cartao d={dados} />)}
    </>
  );
}

function Contas({ d, mes }: { d: Dados; mes: string }) {
  const gasto = toCents(d.rep.gastos_total);
  const receita = toCents(d.rep.receitas_total);
  const saldo = receita - gasto;
  const pend = d.rep.por_categoria.find((c) => c.categoria === SEM_CATEGORIA);
  const estourou = d.bud.itens.find((i) => i.estado === "estourou");
  const atencao = d.bud.itens.find((i) => i.estado === "atencao");
  const orcado = toCents(d.bud.orcado_total);
  const usado = toCents(d.bud.gasto_nas_categorias);
  const pct = orcado > 0 ? Math.min(usado / orcado, 1) : 0;
  const R = 30, C = 2 * Math.PI * R;

  return (
    <>
      <Carrossel d={d} />
      {pend && pend.qtd > 0 && (
        <a className="card alert a-warn rise" href={hrefDe("atividades", { f: "uncat" })}>
          <div className="ic2">?</div>
          <div><b>{pend.qtd} {pend.qtd === 1 ? "lançamento sem categoria" : "lançamentos sem categoria"}</b><small>Toque para classificar</small></div>
        </a>
      )}
      {estourou ? (
        <a className="card alert a-neg rise" href={hrefDe("orcamento")}>
          <div className="ic2">!</div>
          <div><b>{estourou.categoria} estourou o limite</b><small className="n v">{brl(toCents(-estourou.restante))} acima de {brl(toCents(estourou.limite))}</small></div>
        </a>
      ) : atencao ? (
        <a className="card alert a-warn rise" href={hrefDe("orcamento")}>
          <div className="ic2">%</div>
          <div><b>{atencao.categoria} perto do limite</b><small className="n v">faltam {brl(toCents(atencao.restante))}</small></div>
        </a>
      ) : null}

      <div className="grid2">
        <a className="card tint-g rise" href={hrefDe("fluxo")} style={{ ["--i" as string]: 3 }}>
          <div className="flowbars">
            <i style={{ width: "100%", background: "var(--pos)" }} />
            <i style={{ width: `${receita > 0 ? Math.min(100, Math.round((gasto / receita) * 100)) : 0}%`, background: "var(--neg)" }} />
          </div>
          <div className="lbl">Fluxo de caixa</div>
          <div className={`val n v ${saldo < 0 ? "neg" : ""}`}>{brl(saldo, true)}</div>
          <div className="sub n v neg">{brl(-gasto)}</div>
        </a>
        <a className="card tint-v rise" href={hrefDe("atividades", { cat: "Assinaturas" })} style={{ ["--i" as string]: 4 }}>
          <div className="bolha"><Svg d={D.repetir} /></div>
          <div className="lbl">Assinaturas no mês</div>
          <div className="val n v">{brl(toCents(d.ass.total))}</div>
          <div className="sub">{d.ass.itens.length === 0 ? "Nenhuma ativa" : `${d.ass.itens.length} ${d.ass.itens.length === 1 ? "ativa" : "ativas"}`}</div>
        </a>
        <a className="card tint-o rise" href={hrefDe("orcamento")} style={{ ["--i" as string]: 5 }}>
          <svg className="anel" viewBox="0 0 72 72" aria-hidden="true">
            <circle cx="36" cy="36" r={R} fill="none" stroke="var(--edge-2)" strokeWidth="10" />
            <circle cx="36" cy="36" r={R} fill="none" stroke={usado > orcado ? "var(--neg)" : "var(--warn)"} strokeWidth="10" strokeLinecap="round"
              strokeDasharray={`${(pct * C).toFixed(1)} ${C.toFixed(1)}`} transform="rotate(-90 36 36)" />
          </svg>
          <div className="lbl">Orçamento usado</div>
          <div className="val n v">{orcado > 0 ? brl(usado) : "—"}</div>
          <div className="sub n v">{orcado > 0 ? (orcado >= usado ? `Disp: ${brl(orcado - usado)}` : `Acima: ${brl(usado - orcado)}`) : "Sem limites definidos"}</div>
        </a>
        <div className="card rise" style={{ ["--i" as string]: 6 }}>
          <div className="bolha dim"><Svg d={D.parcelas} /></div>
          <div className="lbl">Parcelas a vir</div>
          <div className="val n v">{brl(toCents(d.parc.total))}</div>
          <div className="sub">{d.parc.meses.length === 0 ? "Nenhuma" : `${d.parc.meses.reduce((s, m) => s + m.itens.length, 0)} parcelas`}</div>
        </div>
      </div>

      <GraficoGasto d={d} mes={mes} gasto={gasto} />
      <Categorias d={d} gasto={gasto} />

      <div className="card rise" style={{ padding: "14px 20px", ["--i" as string]: 9 } as React.CSSProperties}>
        <div className="lbl" style={{ paddingTop: 6 }}>Transações recentes</div>
        {d.tx.length === 0 && <p className="sub" style={{ padding: "14px 0" }}>Sem lançamentos neste mês.</p>}
        {d.tx.slice(0, 3).map((t) => <LinhaTx key={t.id} t={t} />)}
      </div>
    </>
  );
}

function Carrossel({ d }: { d: Dados }) {
  const ref = useRef<HTMLDivElement>(null);
  const [slide, setSlide] = useState(0);
  const cartao = toCents(d.rep.gastos_cartao);
  const parcelas = toCents(d.parc.total);
  const slides = parcelas > 0 ? 2 : 1;
  return (
    <>
      <div className="car" ref={ref} onScroll={(e) => { const el = e.currentTarget; setSlide(Math.round(el.scrollLeft / el.clientWidth)); }}>
        <div className="card rise">
          <div className="bank">Cartão de crédito</div>
          <div style={{ padding: "18px 4px 0" }}>
            <div className="lbl">Gasto no cartão neste mês</div>
            <div className="val big n v">{brl(cartao)}</div>
            <div className="sub n v">{brl(toCents(d.rep.gastos_conta))} na conta</div>
          </div>
        </div>
        {parcelas > 0 && (
          <div className="card tint-v">
            <div className="lbl">Já comprometido nas próximas faturas</div>
            <div className="val big n v">{brl(parcelas)}</div>
            <div className="sub">Parcelas restantes das compras parceladas</div>
          </div>
        )}
      </div>
      {slides > 1 && <div className="dots" aria-hidden="true">{Array.from({ length: slides }, (_, k) => <i key={k} className={k === slide ? "on" : ""} />)}</div>}
    </>
  );
}

function GraficoGasto({ d, mes, gasto }: { d: Dados; mes: string; gasto: number }) {
  const W = 340, H = 140;
  const acum = useMemo(() => {
    const hoje = new Date();
    const dias = mes === mesAtual() ? d.daily.dias.filter((x) => x.dia <= hoje.getDate()) : d.daily.dias;
    let s = 0;
    return dias.map((x) => (s += toCents(x.gastos)));
  }, [d.daily, mes]);
  const [sel, setSel] = useState<number | null>(null);
  const n = acum.length;
  if (n < 2) return null;
  const max = Math.max(...acum, 1) * 1.1;
  const X = (k: number) => 6 + (k / (n - 1)) * (W - 18);
  const Y = (v: number) => H - 10 - (v / max) * (H - 30);
  const pts = acum.map((v, k) => [X(k), Y(v)] as const);
  const linha = suave(pts);
  const i = sel ?? n - 1;
  const mover = (e: ReactPointerEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width) * W;
    setSel(Math.max(0, Math.min(n - 1, Math.round(((x - 6) / (W - 18)) * (n - 1)))));
  };
  return (
    <div className="card tint-c rise">
      <div className="lbl">{sel === null ? "Gastos do mês" : `Gasto até o dia ${sel + 1}`}</div>
      <div className="val big n v">{brl(sel === null ? gasto : acum[i]!)}</div>
      <div className="chartwrap" onPointerDown={(e) => { e.currentTarget.setPointerCapture(e.pointerId); mover(e); }}
        onPointerMove={(e) => { if (e.buttons > 0 || e.pointerType === "mouse") mover(e); }}
        onPointerUp={() => setSel(null)} onPointerLeave={() => setSel(null)} onPointerCancel={() => setSel(null)}>
        <div className={`bubble v${sel === null ? "" : " on"}`} style={{ left: `${Math.max(18, Math.min(82, (X(i) / W) * 100))}%` }}>
          Dia {i + 1} · {brl(acum[i]!)}
        </div>
        <svg className="chart" viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Gasto acumulado por dia">
          <defs>
            <linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="var(--accent)" stopOpacity=".45" /><stop offset="1" stopColor="var(--accent)" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path className="areafade" d={`${linha} L${X(n - 1)} ${H - 10} L${X(0)} ${H - 10} Z`} fill="url(#ag)" />
          <path className="draw" pathLength={1} d={linha} fill="none" stroke="var(--accent)" strokeWidth="3" strokeLinecap="round" />
          {sel !== null && <line x1={X(i)} x2={X(i)} y1="14" y2={H - 10} stroke="var(--edge-2)" strokeDasharray="3 4" />}
          <circle cx={X(i)} cy={Y(acum[i]!)} r="6" fill="var(--accent)" stroke="var(--card)" strokeWidth="3" />
        </svg>
      </div>
      <div className="axis"><span>Dia 1</span><span>Dia {n}</span></div>
    </div>
  );
}

function Categorias({ d, gasto }: { d: Dados; gasto: number }) {
  const [sel, setSel] = useState<string | null>(null);
  const itens = d.rep.por_categoria.map((c) => ({ ...c, cents: toCents(c.valor) })).filter((c) => c.cents > 0);
  const atual = itens.find((c) => c.categoria === sel);
  return (
    <div className="card rise">
      <div className="lbl">Gastos por categoria</div>
      <div className="val big n v">{brl(gasto)}</div>
      {itens.length === 0 ? <p className="sub" style={{ paddingTop: 12 }}>Sem gastos neste mês.</p> : (
        <>
          <div className={`seg${sel ? " has" : ""}`}>
            {itens.map((c, k) => (
              <button key={c.categoria} type="button" className={sel === c.categoria ? "pick" : ""} aria-label={`${c.categoria}: ${brl(c.cents)}`}
                aria-pressed={sel === c.categoria} onClick={() => setSel(sel === c.categoria ? null : c.categoria)}
                style={{ flex: c.cents, background: corDaCategoria(c.categoria), animationDelay: `${0.15 + k * 0.07}s` }} />
            ))}
          </div>
          <div className="segline">
            {atual ? (
              <><span><b>{atual.categoria}</b></span><span className="n v">{brl(atual.cents)} · {Math.round((atual.cents / gasto) * 100)}%</span></>
            ) : (
              <><span className="lbl">Toque numa faixa</span><span className="lbl">{itens.length} {itens.length === 1 ? "categoria" : "categorias"}</span></>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function Cartao({ d }: { d: Dados }) {
  return (
    <>
      <div className="card rise">
        <div className="bank">Cartão de crédito</div>
        <div style={{ padding: "18px 4px 0" }}>
          <div className="lbl">Gasto no cartão neste mês</div>
          <div className="val big n v">{brl(toCents(d.rep.gastos_cartao))}</div>
          <div className="sub n v">{brl(toCents(d.rep.gastos_conta))} na conta</div>
        </div>
      </div>
      <div className="card rise" style={{ ["--i" as string]: 1 }}>
        <div className="lbl">Parcelas a vir</div>
        {d.parc.meses.length === 0 && <p className="sub" style={{ paddingTop: 10 }}>Nenhuma parcela restante.</p>}
        {d.parc.meses.slice(0, 3).map((m) => (
          <div className="tx" key={m.mes}>
            <div className="ic">{m.itens.length}</div>
            <div className="t"><b>{nomeDoMes(m.mes)}</b><small>{m.itens.length} {m.itens.length === 1 ? "parcela" : "parcelas"}</small></div>
            <span className="n v">{brl(toCents(m.total))}</span>
          </div>
        ))}
        <p className="sub" style={{ paddingTop: 8, whiteSpace: "normal" }}>Já comprometido no cartão, a partir das parcelas da fatura. Não entra nos gastos do mês.</p>
      </div>
    </>
  );
}
