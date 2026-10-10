"use strict";
/* Arkhe Finance — front em JS puro. Tudo que vem do CSV passa por esc() antes de entrar no HTML. */

const $app = document.getElementById("app");
const $nav = document.getElementById("nav");
const $sheet = document.getElementById("sheet");

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const brl = (v) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const money = (v) => `<span class="money">${brl(v)}</span>`;
const pct = (v) => `${v.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

/* ---------- estado ---------- */
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* sem storage: segue sem lembrar */ } },
};
const now = new Date();
const ymNow = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
const state = { view: "home", month: ymNow, hidden: store.get("hidden", false), filter: "all", q: "", category: null, flow: "geral", cache: {}, months: [] };
document.body.classList.toggle("hide", state.hidden);
state.theme = store.get("theme", "dark") === "light" ? "light" : "dark";  // escuro é o padrão; claro é opcional
const applyTheme = () => {
  document.documentElement.dataset.theme = state.theme;
  const m = document.querySelector('meta[name="theme-color"]'); if (m) m.content = state.theme === "light" ? "#f3f2ee" : "#0c0c0d";
};
applyTheme();
const LOGO = `<svg viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="9" fill="var(--accent)"/><rect x="7" y="17" width="4.5" height="8" rx="2.25" fill="var(--on-accent)"/><rect x="13.75" y="12" width="4.5" height="13" rx="2.25" fill="var(--on-accent)"/><rect x="20.5" y="7" width="4.5" height="18" rx="2.25" fill="var(--on-accent)"/></svg>`;

/* ---------- categorias: cor por entidade (nunca por ranking) e ícone ---------- */
const CATS = {
  "Transporte": [1, "🚗"], "Delivery": [2, "🛵"], "Mercado": [3, "🛒"], "Alimentação": [4, "🍽️"],
  "Saúde": [5, "💊"], "Educação": [6, "🎓"], "Moradia": [7, "🏠"], "Compras": [8, "🛍️"],
  "Celular": [0, "📱"], "Assinaturas": [0, "🔁"], "Lazer": [0, "🎟️"], "Cuidados": [0, "💈"], "Sem categoria": [0, "🏷️"],
};
const catColor = (n) => `var(--c${(CATS[n] || [0])[0]})`;
const catIcon = (n) => (CATS[n] || [0, "•"])[1];
const KIND = {
  expense: "Gasto", income: "Receita", transfer: "Transferência entre contas suas (não conta como gasto)",
  card_payment: "Pagamento de fatura (o gasto está na fatura)", credit_funding: "Pix no crédito (o gasto é o Pix de saída)",
  passthrough: "Repasse: entrou e saiu o mesmo valor (não conta)",
};

/* ---------- ícones (traço simples) ---------- */
const I = (d, extra = "") => `<svg class="i" viewBox="0 0 24 24" aria-hidden="true">${d}${extra}</svg>`;
const ICON = {
  home: I('<path d="M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>'),
  list: I('<path d="M4 6h16M4 12h16M4 18h10"/>'),
  pie: I('<circle cx="12" cy="12" r="9"/><path d="M12 3v9h9"/>'),
  flow: I('<path d="M7 4v14M7 4L4 7M7 4l3 3M17 20V6M17 20l-3-3M17 20l3-3"/>'),
  plus: I('<path d="M12 5v14M5 12h14"/>'),
  eye: I('<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>'),
  eyeOff: I('<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/><path d="M4 4l16 16"/>'),
  left: I('<path d="M15 6l-6 6 6 6"/>'),
  right: I('<path d="M9 6l6 6-6 6"/>'),
  target: I('<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>'),
  sun: I('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
  moon: I('<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"/>'),
  upload: I('<path d="M12 16V4M12 4l-4 4M12 4l4 4M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>'),
  search: I('<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>'),
};

/* ---------- datas ---------- */
const MONTHS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
const ymLabel = (ym) => { const [y, m] = ym.split("-").map(Number); return `${cap(MONTHS[m - 1])} ${y}`; };
const ymShift = (ym, d) => { const [y, m] = ym.split("-").map(Number); const t = new Date(y, m - 1 + d, 1); return `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, "0")}`; };
const parseDay = (iso) => { const [y, m, d] = iso.split("-").map(Number); return new Date(y, m - 1, d); };
const dayLabel = (iso) => {
  const d = parseDay(iso), t0 = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const diff = Math.round((t0 - d) / 864e5);
  if (diff === 0) return "Hoje";
  if (diff === 1) return "Ontem";
  if (diff > 1 && diff < 7) return cap(d.toLocaleDateString("pt-BR", { weekday: "long" }));
  return `${d.getDate()} de ${MONTHS[d.getMonth()].slice(0, 3)}`;
};
const shortDate = (iso) => { const d = parseDay(iso); return `${d.getDate()} de ${MONTHS[d.getMonth()].slice(0, 3)}`; };
const greeting = () => { const h = now.getHours(); return h < 12 ? "Bom dia" : h < 18 ? "Boa tarde" : "Boa noite"; };

/* ---------- dados ---------- */
async function api(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Erro ${r.status}`); }
  return r.json();
}
const qs = (o) => new URLSearchParams(Object.entries(o).filter(([, v]) => v !== null && v !== undefined && v !== "")).toString();
async function monthData(month) {
  if (!state.cache[month]) {
    const [rep, daily, tx, bud] = await Promise.all([
      api(`/reports/monthly?${qs({ month })}`), api(`/reports/daily?${qs({ month })}`),
      api(`/transactions?${qs({ month, kinds: "income,expense", desc: true })}`),
      api(`/budgets?${qs({ month })}`),
    ]);
    state.cache[month] = { rep, daily, tx, bud };
  }
  return state.cache[month];
}
const invalidate = () => { state.cache = {}; };

/* "150", "150,5", "1.500,00", "R$ 99,90" -> número com até 2 casas; inválido -> null */
function parseBRL(texto) {
  if (/-/.test(String(texto))) return null;  // limite negativo nunca vira positivo por engano
  let t = String(texto).replace(/[^\d,.]/g, "");
  if (t.includes(",")) t = t.replace(/\./g, "").replace(",", ".");
  else if (/^\d{1,3}(\.\d{3})+$/.test(t)) t = t.replace(/\./g, "");  // 1.500 = mil e quinhentos
  if (/\.\d{3,}$/.test(t)) return null;  // mais de 2 casas: recusa em vez de arredondar em silêncio
  const v = Number(t);
  return Number.isFinite(v) && v > 0 ? Math.round(v * 100) / 100 : null;
}
const ESTADO = {
  ok: { rotulo: "Dentro do limite", icone: "✓" },
  atencao: { rotulo: "Atenção", icone: "⚠" },
  estourou: { rotulo: "Estourou", icone: "⛔" },
};
const meter = (i) => `<div class="meter ${i.estado}" role="img" aria-label="${pct(i.percentual)} do limite"><i style="width:${Math.min(100, i.percentual)}%"></i></div>`;
const budgetRow = (i, extra = "") => `<button class="item bud" data-bud="${esc(i.categoria)}" data-limite="${i.limite}"><span class="ico sm" style="--cc:${catColor(i.categoria)}">${catIcon(i.categoria)}</span>
  <span class="grow"><div class="row between"><span class="nm">${esc(i.categoria)}</span><span class="small st-${i.estado}">${ESTADO[i.estado].icone} ${ESTADO[i.estado].rotulo}</span></div>
  ${meter(i)}<div class="muted small bud-l">${money(i.gasto)} de ${money(i.limite)}${i.restante < 0 ? ` · passou ${money(-i.restante)}` : ` · restam ${money(i.restante)}`}</div></span></button>`;

/* ---------- gráficos ---------- */
const cumulative = (arr, n) => { let s = 0; return Array.from({ length: n }, (_, i) => (s += arr[i] || 0)); };

function monotonePath(pts) { // interpolação monotônica: suave, sem "ondas" fora dos dados
  const n = pts.length; if (n < 2) return "";
  const dx = [], m = [], t = [];
  for (let i = 0; i < n - 1; i++) { dx[i] = pts[i + 1][0] - pts[i][0]; m[i] = (pts[i + 1][1] - pts[i][1]) / (dx[i] || 1); }
  t[0] = m[0]; t[n - 1] = m[n - 2];
  for (let i = 1; i < n - 1; i++) t[i] = m[i - 1] * m[i] <= 0 ? 0 : (m[i - 1] + m[i]) / 2;
  for (let i = 0; i < n - 1; i++) if (m[i] === 0) t[i] = t[i + 1] = 0;
  let d = `M${pts[0][0]},${pts[0][1]}`;
  for (let i = 0; i < n - 1; i++) {
    const h = dx[i] / 3;
    d += ` C${pts[i][0] + h},${pts[i][1] + t[i] * h} ${pts[i + 1][0] - h},${pts[i + 1][1] - t[i + 1] * h} ${pts[i + 1][0]},${pts[i + 1][1]}`;
  }
  return d;
}

/* Linha acumulada: mês atual (sólido) x anterior (tracejado). `mini` = versão do cartão da Início. */
function lineChart({ cur, prev, upto, mini = false }) {
  const W = 340, H = mini ? 110 : 190, pad = 8, n = prev.length;
  const max = Math.max(1, ...cur.slice(0, upto), ...prev) * 1.08;
  const x = (i) => pad + (i / Math.max(1, n - 1)) * (W - 2 * pad);
  const y = (v) => H - pad - (v / max) * (H - 2 * pad);
  const curPts = cur.slice(0, upto).map((v, i) => [x(i), y(v)]);
  const prevPts = prev.map((v, i) => [x(i), y(v)]);
  const last = curPts[curPts.length - 1] || [x(0), y(0)];
  const area = `${monotonePath(curPts)} L${last[0]},${H - pad} L${curPts[0][0]},${H - pad} Z`;
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Gasto acumulado no mês: ${brl(cur[upto - 1] || 0)}">
    <defs><linearGradient id="g${mini ? "m" : "b"}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--accent)" stop-opacity=".28"/><stop offset="1" stop-color="var(--accent)" stop-opacity="0"/></linearGradient></defs>
    <line x1="${pad}" x2="${W - pad}" y1="${H - pad}" y2="${H - pad}" stroke="var(--line)"/>
    ${mini ? "" : `<path d="${monotonePath(prevPts)}" fill="none" stroke="var(--muted)" stroke-width="2" stroke-dasharray="5 5" stroke-linecap="round"/>`}
    <path d="${area}" fill="url(#g${mini ? "m" : "b"})"/>
    <path d="${monotonePath(curPts)}" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="${last[0]}" cy="${last[1]}" r="5" fill="var(--accent)" stroke="var(--card)" stroke-width="2"/>
    <g id="xh" style="display:none"><line y1="${pad}" y2="${H - pad}" stroke="var(--muted)" stroke-dasharray="3 3"/><circle r="5" fill="var(--accent)" stroke="var(--card)" stroke-width="2"/></g>
  </svg>`;
}

/* Crosshair + tooltip por dia (mouse e toque). */
function wireHover(box, { cur, prev, upto, month }) {
  const svg = box.querySelector("svg"), g = svg.querySelector("#xh"), tip = box.querySelector(".tip");
  const W = 340, pad = 8, n = prev.length, vb = svg.viewBox.baseVal;
  const show = (ev) => {
    const r = svg.getBoundingClientRect();
    const px = ((ev.clientX - r.left) / r.width) * W;
    const i = Math.max(0, Math.min(upto - 1, Math.round(((px - pad) / (W - 2 * pad)) * (n - 1))));
    const cx = pad + (i / Math.max(1, n - 1)) * (W - 2 * pad);
    const max = Math.max(1, ...cur.slice(0, upto), ...prev) * 1.08, cy = vb.height - pad - (cur[i] / max) * (vb.height - 2 * pad);
    g.style.display = ""; g.querySelector("line").setAttribute("x1", cx); g.querySelector("line").setAttribute("x2", cx);
    g.querySelector("circle").setAttribute("cx", cx); g.querySelector("circle").setAttribute("cy", cy);
    tip.hidden = false; tip.style.left = `${(cx / W) * r.width}px`; tip.style.top = `${(cy / vb.height) * r.height}px`;
    tip.innerHTML = `<b>${i + 1} de ${MONTHS[Number(month.slice(5)) - 1].slice(0, 3)}</b><br>${money(cur[i])}<br><span class="muted">mês anterior: ${money(prev[i] ?? 0)}</span>`;
  };
  const hide = () => { g.style.display = "none"; tip.hidden = true; };
  box.addEventListener("pointermove", show); box.addEventListener("pointerdown", show);
  box.addEventListener("pointerleave", hide); box.addEventListener("pointercancel", hide);
}

/* Rosca com pontas arredondadas. Máximo de 6 categorias + "Outros" (cinza); a lista abaixo é a legenda. */
function donut(rows, total) {
  const R = 90, C = 2 * Math.PI * R, SW = 18, GAP = 4;
  let acc = 0;
  const segs = rows.map((r) => {
    const f = total ? r.valor / total : 0, len = Math.max(0.01, f * C - SW - GAP), off = -(acc * C + SW / 2 + GAP / 2);
    acc += f;
    return `<circle cx="110" cy="110" r="${R}" fill="none" stroke="${r.cor}" stroke-width="${SW}" stroke-linecap="round" stroke-dasharray="${len} ${C}" stroke-dashoffset="${off}" transform="rotate(-90 110 110)"><title>${esc(r.nome)}: ${brl(r.valor)}</title></circle>`;
  }).join("");
  return `<svg class="donut" viewBox="0 0 220 220" role="img" aria-label="Gastos por categoria">
    <circle cx="110" cy="110" r="${R}" fill="none" stroke="var(--card-2)" stroke-width="${SW}"/>${segs}
    <text x="110" y="108" text-anchor="middle" fill="var(--text)" font-size="21" font-weight="800" class="money">${esc(brl(total).replace(/\s/g, " "))}</text>
    <text x="110" y="132" text-anchor="middle" fill="var(--muted)" font-size="12">gastos no mês</text></svg>`;
}

/* ---------- peças de UI ---------- */
const hdrButtons = () => `<div class="row" style="gap:8px"><button class="round" data-act="theme" aria-label="${state.theme === "dark" ? "Usar tema claro" : "Usar tema escuro"}">${state.theme === "dark" ? ICON.sun : ICON.moon}</button><button class="round" data-act="eye" aria-label="${state.hidden ? "Mostrar valores" : "Ocultar valores"}">${state.hidden ? ICON.eyeOff : ICON.eye}</button></div>`;
const monthPill = () => `<div class="pill"><button data-act="prev" aria-label="Mês anterior">${ICON.left}</button><span>${ymLabel(state.month)}</span><button data-act="next" aria-label="Próximo mês" ${state.month >= ymNow ? "disabled style='opacity:.3'" : ""}>${ICON.right}</button></div>`;
const backHdr = (extra = "") => `<div class="hdr"><button class="round" data-go="home" aria-label="Voltar">${ICON.left}</button><div class="row">${extra}${hdrButtons()}</div></div>`;
const prettyName = (t) => (t.account === "nubank_conta" && t.counterparty)
  ? t.counterparty.toLowerCase().replace(/(^|\s)\S/g, (c) => c.toUpperCase()) : t.description;
const txRow = (t) => {
  const inc = t.amount_cents > 0, hiddenKind = !["expense", "income"].includes(t.kind);
  const acct = t.account === "nubank_fatura" ? " • Cartão" : "";
  return `<button class="item" data-tx="${t.id}"><span class="ico" style="--cc:${catColor(t.category)}">${hiddenKind ? "↔" : catIcon(t.category)}</span>
    <span class="grow"><div class="nm">${esc(prettyName(t))}</div><div class="muted small">${shortDate(t.date)} • ${esc(hiddenKind ? "Não conta" : t.category)}${acct}</div></span>
    <span class="amt ${hiddenKind ? "muted" : inc ? "pos" : "neg"}"><span class="money">${inc ? "+" : "−"}${brl(Math.abs(t.amount_cents) / 100)}</span></span></button>`;
};
function catRows(rep) {
  const total = rep.gastos_total || 0;
  return rep.por_categoria.map((c) => ({ nome: c.categoria, valor: c.valor, qtd: c.qtd, cor: catColor(c.categoria), pct: total ? (c.valor / total) * 100 : 0 }));
}

/* ---------- telas ---------- */
async function viewHome() {
  const { rep, daily, tx, bud } = await monthData(state.month);
  const n = daily.anterior.length, upto = state.month === ymNow ? Math.min(now.getDate(), n) : n;
  const cur = cumulative(daily.dias.map((d) => d.gastos), n), prev = cumulative(daily.anterior.map((d) => d.gastos), n);
  const cats = catRows(rep), pend = cats.find((c) => c.nome === "Sem categoria");
  const top = cats.slice(0, 3), rest = cats.length - top.length;
  const saldo = rep.receitas_total - rep.gastos_total;
  return `<div class="brand brand-m">${LOGO}<span>Arkhe Finance</span></div>
  <div class="hdr">${monthPill()}${hdrButtons()}</div>
  <h1 class="greet">${greeting()} 👋</h1>
  <div class="stack">
    ${pend ? `<button class="card full" data-go="activity" data-filter="uncat"><div class="lbl"><span>Para categorizar</span>${ICON.right}</div>
      <div class="mid" style="margin-top:6px">${pend.qtd} ${pend.qtd === 1 ? "transação" : "transações"} · ${money(pend.valor)}</div><div class="muted small">Toque para classificar</div></button>` : ""}
    <button class="card" data-go="spend"><div class="lbl"><span>Gastos do mês</span>${ICON.right}</div>
      <div class="big">${money(rep.gastos_total)}</div>${lineChart({ cur, prev, upto, mini: true })}</button>
    <div class="card"><div class="lbl"><span>Categorias</span></div>
      <div class="seg" role="img" aria-label="Distribuição dos gastos">${top.map((c) => `<i style="flex:${c.valor};--cc:${c.cor}"></i>`).join("") || `<i style="flex:1;--cc:var(--card-2)"></i>`}</div>
      ${top.map((c) => `<button class="item" data-go="activity" data-cat="${esc(c.nome)}"><span class="ico sm" style="--cc:${c.cor}">${catIcon(c.nome)}</span><span class="grow"><div class="nm">${esc(c.nome)}</div><div class="muted small">${pct(c.pct)}</div></span><span class="amt">${money(c.valor)}</span></button>`).join("") || `<p class="empty">Sem gastos neste mês.</p>`}
      ${rest > 0 ? `<button class="item" data-go="spend" style="justify-content:center"><span class="muted">Ver mais ${rest} ${rest === 1 ? "categoria" : "categorias"}</span></button>` : ""}</div>
    <button class="card" data-go="budget"><div class="lbl"><span>Orçamento</span>${ICON.right}</div>
      ${bud.itens.length ? bud.itens.slice(0, 3).map((i) => `<div class="bud-mini"><div class="row between"><span class="nm">${catIcon(i.categoria)} ${esc(i.categoria)}</span><span class="small st-${i.estado}">${ESTADO[i.estado].icone} ${pct(i.percentual)}</span></div>${meter(i)}</div>`).join("")
        : `<p class="t2" style="margin-top:8px">Defina um limite por categoria e acompanhe quanto ainda pode gastar.</p><p class="small" style="margin-top:6px;color:var(--accent)">Criar orçamento</p>`}</button>
    <div class="card"><button class="lbl" data-go="activity" style="width:100%"><span>Transações recentes</span>${ICON.right}</button>
      ${tx.slice(0, 5).map(txRow).join("") || `<p class="empty">${state.months.length ? "Sem lançamentos neste mês. Volte para outro mês ou use a aba Importar." : "Nada importado ainda. Use a aba Importar para começar."}</p>`}</div>
    <div class="grid2">
      <button class="card" data-go="flow"><div class="lbl"><span>Fluxo</span>${ICON.right}</div><div class="mid" style="margin-top:8px"><span class="${saldo >= 0 ? "pos" : "neg"}">${money(saldo)}</span></div>
        <div class="muted small" style="margin-top:6px">Receitas − gastos</div></button>
      <button class="card" data-go="activity" data-filter="card"><div class="lbl"><span>Cartão</span>${ICON.right}</div><div class="mid" style="margin-top:8px">${money(rep.gastos_cartao)}</div>
        <div class="muted small" style="margin-top:6px">Gasto na fatura</div></button>
    </div>
  </div>`;
}

async function viewSpend() {
  const { rep, daily } = await monthData(state.month);
  const n = daily.anterior.length, upto = state.month === ymNow ? Math.min(now.getDate(), n) : n;
  const cur = cumulative(daily.dias.map((d) => d.gastos), n), prev = cumulative(daily.anterior.map((d) => d.gastos), n);
  const here = cur[upto - 1] || 0, before = prev[upto - 1] || 0, d = before ? ((here - before) / before) * 100 : null;
  const cats = catRows(rep), own = (c) => (CATS[c.nome] || [0])[0] > 0;
  const colored = cats.filter(own).slice(0, 6), pending = cats.find((c) => c.nome === "Sem categoria");
  const other = cats.filter((c) => c !== pending && !colored.includes(c)).reduce((s, c) => s + c.valor, 0);
  const segs = colored.map((c) => ({ nome: c.nome, valor: c.valor, cor: c.cor }))
    .concat(pending ? [{ nome: "Sem categoria", valor: pending.valor, cor: "var(--c0)" }] : [])
    .concat(other > 0 ? [{ nome: "Outras categorias", valor: other, cor: "var(--other)" }] : []);
  return `${backHdr(monthPill())}
  <p class="muted">Gastos em ${cap(MONTHS[Number(state.month.slice(5)) - 1])}</p>
  <div class="title" style="font-size:2.6rem">${money(rep.gastos_total)}</div>
  ${d === null ? `<p class="delta muted">Sem mês anterior para comparar</p>` : `<p class="delta"><span class="${d <= 0 ? "down" : "up"}">${d <= 0 ? "↓" : "↑"} ${pct(Math.abs(d))}</span> <span class="t2">vs ${money(before)} no mesmo ponto do mês anterior</span></p>`}
  <div class="legend"><span><i></i>Este mês</span><span><i class="d"></i>Mês anterior</span></div>
  <div class="chart" id="chart">${lineChart({ cur, prev, upto })}<div class="tip" hidden></div></div>
  <div class="axis"><span>01</span><span>${String(Math.ceil(n / 2)).padStart(2, "0")}</span><span>${String(n).padStart(2, "0")}</span></div>
  <details><summary>Ver valores por dia</summary><table><tr><th>Dia</th><th>Gasto</th></tr>${daily.dias.filter((x) => x.gastos > 0).map((x) => `<tr><td>${x.dia}</td><td>${money(x.gastos)}</td></tr>`).join("") || "<tr><td colspan=2>Sem gastos</td></tr>"}</table></details>
  <h2 style="margin:26px 0 0;font-size:1.1rem">Categorias</h2>${donut(segs, rep.gastos_total)}
  <div>${cats.map((c) => `<button class="item" data-go="activity" data-cat="${esc(c.nome)}"><span class="ico" style="--cc:${c.cor}">${catIcon(c.nome)}</span><span class="grow"><div class="nm">${esc(c.nome)}</div><div class="muted small">${pct(c.pct)} · ${c.qtd} ${c.qtd === 1 ? "transação" : "transações"}</div></span><span class="amt">${money(c.valor)}</span></button>`).join("") || `<p class="empty">Sem gastos neste mês.</p>`}</div>`;
}

async function viewActivity() {
  const f = state.filter, base = { month: state.month, desc: true, q: state.q };
  const params = state.category ? { ...base, kinds: "expense,income", category: state.category }
    : f === "in" ? { ...base, kind: "income" } : f === "out" ? { ...base, kind: "expense" }
    : f === "uncat" ? { ...base, kind: "expense", category: "Sem categoria" }
    : f === "hidden" ? { ...base, kinds: "passthrough,transfer,card_payment,credit_funding" }
    : { ...base, kinds: "income,expense" };
  let list = await api(`/transactions?${qs(params)}`);
  if (f === "card") list = list.filter((t) => t.account === "nubank_fatura");
  const groups = []; list.forEach((t) => { const g = groups[groups.length - 1]; (g && g.date === t.date ? g : groups[groups.push({ date: t.date, items: [] }) - 1]).items.push(t); });
  const chip = (k, label) => `<button class="chip" data-filter="${k}" aria-pressed="${!state.category && f === k}">${label}</button>`;
  return `<div class="hdr"><h1 class="title">Atividades</h1>${monthPill()}</div>
  <button class="chip" data-go="rules" style="margin-bottom:10px">Regras de categoria</button>
  <label class="search">${ICON.search}<input id="q" type="search" placeholder="Buscar" value="${esc(state.q)}" aria-label="Buscar transações" autocomplete="off"></label>
  <div class="chips">${chip("all", "Todas")}${chip("in", "Entradas")}${chip("out", "Saídas")}${chip("uncat", "Sem categoria")}${chip("card", "Cartão")}${chip("hidden", "Não contam")}</div>
  ${state.category ? `<button class="chip" data-clearcat style="margin-bottom:6px" aria-pressed="true">${esc(state.category)} ✕</button>` : ""}
  ${groups.map((g) => `<div class="day">${dayLabel(g.date)}</div>${g.items.map(txRow).join("")}`).join("") || `<p class="empty">Nada por aqui.</p>`}`;
}

async function viewFlow() {
  const { rep, daily, tx } = await monthData(state.month);
  const mode = state.flow, saldo = rep.receitas_total - rep.gastos_total;
  const W = 34 * daily.dias.length + 20, H = 190, base = H - 22;
  const max = Math.max(1, ...daily.dias.map((d) => (mode === "entradas" ? d.entradas : mode === "saidas" ? d.gastos : Math.max(d.entradas, d.gastos))));
  const h = (v) => (v / max) * (base - 14);
  const bars = daily.dias.map((d, i) => {
    const x = 12 + i * 34, one = mode !== "geral";
    const val = mode === "entradas" ? d.entradas : d.gastos;
    const bar = (cx, v, color, label) => v > 0
      ? `<rect x="${cx}" y="${base - h(v)}" width="10" height="${h(v)}" rx="5" fill="${color}"><title>${d.dia}: ${label} ${brl(v)}</title></rect>`
      : `<circle cx="${cx + 5}" cy="${base - 5}" r="4" fill="none" stroke="var(--line)" stroke-dasharray="2 2"/>`;
    const col = (m) => (m === "entradas" ? "var(--pos)" : "var(--neg)");
    return (one ? bar(x + 7, val, col(mode), mode === "entradas" ? "entradas" : "gastos") : bar(x, d.entradas, "var(--pos)", "entradas") + bar(x + 14, d.gastos, "var(--neg)", "gastos"))
      + `<text x="${x + 12}" y="${H - 4}" text-anchor="middle" fill="var(--muted)" font-size="10">${String(d.dia).padStart(2, "0")}</text>`;
  }).join("");
  const mk = (k, label) => `<button class="chip" data-flow="${k}" aria-pressed="${mode === k}">${label}</button>`;
  return `${backHdr(monthPill())}
  <div class="chips" style="margin-top:0">${mk("geral", "Geral")}${mk("entradas", "Entradas")}${mk("saidas", "Saídas")}</div>
  <p class="muted" style="margin-top:14px">Fluxo geral em ${cap(MONTHS[Number(state.month.slice(5)) - 1])}</p>
  <div class="title" style="font-size:2.6rem"><span class="${saldo >= 0 ? "pos" : "neg"}">${money(saldo)}</span></div>
  <p class="t2" style="margin-top:8px"><span class="pos">●</span> Entradas ${money(rep.receitas_total)}<br><span class="neg">●</span> Gastos ${money(rep.gastos_total)}</p>
  <p class="muted small" style="margin:10px 0">Não conta Pix de ida e volta, transferências entre suas contas nem pagamento de fatura.</p>
  <div class="scrollx"><svg viewBox="0 0 ${W} ${H}" width="${W}" role="img" aria-label="Entradas e gastos por dia" style="display:block;min-width:100%"><line x1="0" x2="${W}" y1="${base}" y2="${base}" stroke="var(--line)"/>${bars}</svg></div>
  <h2 style="margin:24px 0 0;font-size:1.1rem">Últimos lançamentos</h2>${tx.slice(0, 6).map(txRow).join("") || `<p class="empty">Sem lançamentos.</p>`}`;
}

async function viewBudget() {
  const { bud } = await monthData(state.month);
  const por = { estourou: 0, atencao: 0, ok: 0 }; bud.itens.forEach((i) => { por[i.estado] += 1; });
  const resumo = bud.itens.length ? `${por.estourou ? `${por.estourou} estourou` : ""}${por.estourou && por.atencao ? " · " : ""}${por.atencao ? `${por.atencao} em atenção` : ""}${!por.estourou && !por.atencao ? "Tudo dentro do limite" : ""}` : "";
  return `<div class="hdr"><h1 class="title">Orçamento</h1>${monthPill()}</div>
  ${bud.itens.length ? `<div class="card"><div class="lbl"><span>Orçado no mês</span></div><div class="big">${money(bud.orcado_total)}</div>
    <p class="t2">Gasto nessas categorias: ${money(bud.gasto_nas_categorias)}</p><p class="small" style="margin-top:6px">${resumo}</p></div>` : ""}
  <div style="margin-top:8px">${bud.itens.map((i) => budgetRow(i)).join("") || `<p class="empty">Nenhum orçamento ainda.<br>Escolha uma categoria e um limite mensal.</p>`}</div>
  <button class="btn" data-bud="" style="margin-top:18px">Novo orçamento</button>
  <p class="muted small" style="margin-top:14px">O limite vale todos os meses. Atenção a partir de 80%; estourou quando passa do limite. Só conta gasto: repasse, transferência e pagamento de fatura ficam de fora.</p>`;
}

let rulesCache = [];
async function viewRules() {
  rulesCache = await api("/rules");
  const ord = [...rulesCache].sort((a, b) => a.category.localeCompare(b.category, "pt-BR") || a.pattern.localeCompare(b.pattern, "pt-BR"));
  const row = (r) => `<button class="item bud" data-rule="${r.id}"><span class="ico sm" style="--cc:${catColor(r.category)}">${catIcon(r.category)}</span>
    <span class="grow"><div class="row between"><span class="nm">${esc(r.pattern)}</span><span class="muted small">${r.priority ? `prioridade ${r.priority}` : ""}</span></div>
    <div class="muted small">vira ${esc(r.category)}</div></span></button>`;
  return `<div class="hdr"><button class="round" data-go="activity" aria-label="Voltar">${ICON.left}</button><div class="row">${hdrButtons()}</div></div>
  <h1 class="title" style="margin-bottom:6px">Regras de categoria</h1>
  <p class="t2 small" style="margin-bottom:14px">Se o nome do lançamento contém o texto, ele entra na categoria. Em caso de várias regras, vence a de maior prioridade; empatando, a mais específica. Categoria escolhida à mão em um lançamento nunca é alterada por regra.</p>
  <button class="btn" data-rule="">Nova regra</button>
  <div style="margin-top:12px">${ord.map(row).join("") || `<p class="empty">Nenhuma regra ainda.</p>`}</div>`;
}
async function openRuleSheet(id) {
  const r = rulesCache.find((x) => x.id === id), novo = !r;
  const cats = (await api("/categories")).filter((c) => c !== "Sem categoria");
  $sheet.innerHTML = `<div class="sheet" role="dialog" aria-modal="true" aria-label="Regra de categoria">
    <div class="row between"><b style="font-size:1.2rem">${novo ? "Nova regra" : "Editar regra"}</b><button class="round" data-close aria-label="Fechar">✕</button></div>
    <label class="muted small" for="rpat" style="display:block;margin-top:14px">Quando o nome contém</label>
    <input id="rpat" type="text" value="${esc(r?.pattern)}" placeholder="Ex.: ifood" autocomplete="off">
    <label class="muted small" for="rcat" style="display:block;margin-top:6px">Categoria</label>
    <input id="rcat" type="text" list="rlist" value="${esc(r?.category)}" placeholder="Ex.: Delivery" autocomplete="off">
    <datalist id="rlist">${cats.map((c) => `<option value="${esc(c)}">`).join("")}</datalist>
    <label class="muted small" for="rpri" style="display:block;margin-top:6px">Prioridade (maior vence; padrão 0)</label>
    <input id="rpri" type="number" inputmode="numeric" step="1" value="${r ? r.priority : 0}">
    <p id="rerr" class="neg small" role="alert" style="min-height:1.2em"></p>
    <button class="btn" data-rulesave="${novo ? "" : r.id}">Salvar</button>
    ${novo ? "" : `<button class="chip" data-ruledel="${r.id}" style="width:100%;margin-top:10px;color:var(--neg)">Apagar regra</button>`}</div>`;
  $sheet.hidden = false; document.getElementById("rpat").focus();
}

function viewImport() {
  return `${backHdr()}<h1 class="title" style="margin-bottom:6px">Importar</h1>
  <p class="t2" style="margin-bottom:18px">CSV da conta ou da fatura do Nubank. O app reconhece o tipo e ignora o que já foi importado.</p>
  <label class="drop" id="drop"><input id="file" type="file" accept=".csv,text/csv" multiple hidden><div style="font-size:2rem">📄</div><b>Escolher arquivos CSV</b><div class="muted small" style="margin-top:6px">ou arraste e solte aqui</div></label>
  <div id="res" class="stack" style="margin-top:16px"></div>`;
}

/* ---------- folha de categoria ---------- */
async function openSheet(id) {
  const t = Object.values(state.cache).flatMap((c) => c.tx).find((x) => x.id === id) || (await api(`/transactions?${qs({ month: state.month })}`)).find((x) => x.id === id);
  if (!t) return;
  const cats = await api("/categories");
  const chips = [...new Set([...cats, "Família", "Pessoas"])].sort();
  $sheet.innerHTML = `<div class="sheet" role="dialog" aria-modal="true" aria-label="Categorizar transação">
    <div class="row between"><b style="font-size:1.2rem">${esc(prettyName(t))}</b><button class="round" data-close aria-label="Fechar">✕</button></div>
    <div class="mid" style="margin:10px 0 4px"><span class="${t.amount_cents > 0 ? "pos" : "neg"}">${money(Math.abs(t.amount_cents) / 100)}</span></div>
    <p class="muted small">${shortDate(t.date)} · ${esc(KIND[t.kind] || t.kind)}</p>
    <p class="t2 small" style="margin:10px 0;word-break:break-word">${esc(t.description)}</p>
    <label class="muted small" for="cat">Categoria</label>
    <input id="cat" type="text" list="catlist" value="${esc(t.category === "Sem categoria" ? "" : t.category)}" placeholder="Ex.: Transporte" autocomplete="off">
    <datalist id="catlist">${chips.map((c) => `<option value="${esc(c)}">`).join("")}</datalist>
    <div class="chips">${chips.slice(0, 12).map((c) => `<button class="chip" data-pick="${esc(c)}">${catIcon(c)} ${esc(c)}</button>`).join("")}</div>
    <label class="row" style="margin:12px 0"><input id="rem" type="checkbox" checked> <span>Lembrar para o mesmo nome (cria uma regra)</span></label>
    <button class="btn" data-save="${t.id}">Salvar</button></div>`;
  $sheet.hidden = false; document.getElementById("cat").focus();
}
async function openBudgetSheet(categoria, limite) {
  const cats = (await api("/categories")).filter((c) => c !== "Sem categoria");
  const novo = !categoria;
  $sheet.innerHTML = `<div class="sheet" role="dialog" aria-modal="true" aria-label="Orçamento">
    <div class="row between"><b style="font-size:1.2rem">${novo ? "Novo orçamento" : "Editar orçamento"}</b><button class="round" data-close aria-label="Fechar">✕</button></div>
    <label class="muted small" for="bcat" style="display:block;margin-top:14px">Categoria</label>
    <input id="bcat" type="text" list="blist" value="${esc(categoria)}" placeholder="Ex.: Delivery" autocomplete="off" ${novo ? "" : "readonly"}>
    <datalist id="blist">${cats.map((c) => `<option value="${esc(c)}">`).join("")}</datalist>
    <label class="muted small" for="blim" style="display:block;margin-top:6px">Limite por mês (R$)</label>
    <input id="blim" type="text" inputmode="decimal" value="${limite ? String(limite).replace(".", ",") : ""}" placeholder="Ex.: 150,00" autocomplete="off">
    <p id="berr" class="neg small" role="alert" style="min-height:1.2em"></p>
    <button class="btn" data-budsave>Salvar</button>
    ${novo ? "" : `<button class="chip" data-buddel="${esc(categoria)}" style="width:100%;margin-top:10px;color:var(--neg)">Remover orçamento</button>`}</div>`;
  $sheet.hidden = false; document.getElementById(novo ? "bcat" : "blim").focus();
}
const closeSheet = () => { $sheet.hidden = true; $sheet.innerHTML = ""; };

/* ---------- navegação e render ---------- */
const VIEWS = { home: viewHome, spend: viewSpend, activity: viewActivity, budget: viewBudget, flow: viewFlow, import: viewImport, rules: viewRules };
function renderNav() {
  const t = (v, ic, label) => `<button class="tab" data-go="${v}" ${state.view === v ? 'aria-current="page"' : ""}>${ICON[ic]}<span>${label}</span></button>`;
  $nav.innerHTML = `<div class="brand">${LOGO}<span>Arkhe Finance</span></div><div class="tabs">${t("home", "home", "Início")}${t("activity", "list", "Atividades")}${t("spend", "pie", "Gastos")}${t("budget", "target", "Orçamento")}${t("flow", "flow", "Fluxo")}${t("import", "upload", "Importar")}</div>`;
}
async function render() {
  renderNav();
  try {
    $app.dataset.view = state.view;
    $app.innerHTML = await VIEWS[state.view]();
  } catch (e) {
    $app.innerHTML = `<div class="card"><b>Não foi possível carregar</b><p class="muted" style="margin-top:6px">${esc(e.message)}</p><button class="btn" style="margin-top:14px" data-go="home">Tentar de novo</button></div>`;
    return;
  }
  if (state.view === "spend") {
    const { daily } = await monthData(state.month);
    const n = daily.anterior.length, upto = state.month === ymNow ? Math.min(now.getDate(), n) : n;
    wireHover(document.getElementById("chart"), { cur: cumulative(daily.dias.map((d) => d.gastos), n), prev: cumulative(daily.anterior.map((d) => d.gastos), n), upto, month: state.month });
  }
}
const go = (view, opts = {}) => {
  state.view = view; state.category = opts.cat ?? null;
  if (view === "activity") { state.filter = opts.filter || "all"; if (!opts.keepQ) state.q = ""; }
  window.scrollTo(0, 0); render();
};

async function upload(files) {
  const res = document.getElementById("res");
  res.innerHTML = "";
  for (const f of files) {
    const fd = new FormData(); fd.append("file", f);
    try {
      const r = await api("/import", { method: "POST", body: fd });
      res.insertAdjacentHTML("beforeend", `<div class="card"><b>${esc(f.name)}</b><p class="t2 small" style="margin-top:4px">${r.formato === "nubank_fatura" ? "Fatura do cartão" : "Conta"} · ${r.novas} novas, ${r.duplicadas} já importadas</p></div>`);
    } catch (e) {
      res.insertAdjacentHTML("beforeend", `<div class="card"><b>${esc(f.name)}</b><p class="neg small" style="margin-top:4px">${esc(e.message)}</p></div>`);
    }
  }
  invalidate();
  try { state.months = await api("/months"); } catch { /* segue com a lista antiga */ }
  res.insertAdjacentHTML("beforeend", `<button class="btn" data-go="home">Ver resumo</button>`);
}

let searchTimer;
document.addEventListener("click", async (ev) => {
  const el = ev.target.closest("[data-go],[data-act],[data-tx],[data-filter],[data-flow],[data-close],[data-pick],[data-save],[data-clearcat],[data-bud],[data-budsave],[data-buddel],[data-rule],[data-rulesave],[data-ruledel]");
  if (!el) { if (ev.target === $sheet) closeSheet(); return; }
  const d = el.dataset;
  if (d.close !== undefined) return closeSheet();
  if (d.bud !== undefined) return openBudgetSheet(d.bud, d.limite ? Number(d.limite) : null);
  if (d.budsave !== undefined) {
    const cat = document.getElementById("bcat").value.trim(), lim = parseBRL(document.getElementById("blim").value), err = document.getElementById("berr");
    if (!cat) { err.textContent = "Escolha uma categoria."; return; }
    if (lim === null) { err.textContent = "Informe um limite maior que zero, como 150 ou 150,50."; return; }
    try { await api(`/budgets/${encodeURIComponent(cat)}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ limite: lim }) }); invalidate(); closeSheet(); render(); }
    catch (e) { err.textContent = e.message; }
    return;
  }
  if (d.buddel !== undefined) {
    if (!confirm(`Remover o orçamento de ${d.buddel}? Os lançamentos continuam.`)) return;
    try { await api(`/budgets/${encodeURIComponent(d.buddel)}`, { method: "DELETE" }); invalidate(); closeSheet(); render(); } catch (e) { alert(e.message); }
    return;
  }
  if (d.rule !== undefined) return openRuleSheet(d.rule ? Number(d.rule) : null);
  if (d.rulesave !== undefined) {
    const pattern = document.getElementById("rpat").value.trim(), category = document.getElementById("rcat").value.trim();
    const priority = Number.parseInt(document.getElementById("rpri").value, 10), err = document.getElementById("rerr");
    if (!pattern) { err.textContent = "Escreva o texto que a regra procura."; return; }
    if (!category) { err.textContent = "Escolha uma categoria."; return; }
    if (Number.isNaN(priority)) { err.textContent = "Prioridade precisa ser um número inteiro."; return; }
    try {
      await api(d.rulesave ? `/rules/${d.rulesave}` : "/rules", { method: d.rulesave ? "PUT" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ pattern, category, priority }) });
      invalidate(); closeSheet(); render();
    } catch (e) { err.textContent = e.message; }
    return;
  }
  if (d.ruledel !== undefined) {
    if (!confirm("Apagar esta regra? Os lançamentos voltam a ser categorizados pelas outras regras; os que você categorizou à mão não mudam.")) return;
    try { await api(`/rules/${d.ruledel}`, { method: "DELETE" }); invalidate(); closeSheet(); render(); } catch (e) { alert(e.message); }
    return;
  }
  if (d.pick !== undefined) { document.getElementById("cat").value = d.pick; return; }
  if (d.save !== undefined) {
    const category = document.getElementById("cat").value.trim();
    if (!category) { document.getElementById("cat").focus(); return; }
    try {
      await api(`/transactions/${d.save}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ category, remember: document.getElementById("rem").checked }) });
      invalidate(); closeSheet(); render();
    } catch (e) { alert(e.message); }
    return;
  }
  if (d.tx) return openSheet(Number(d.tx));
  if (d.act === "theme") { state.theme = state.theme === "dark" ? "light" : "dark"; store.set("theme", state.theme); applyTheme(); return render(); }
  if (d.act === "eye") { state.hidden = !state.hidden; store.set("hidden", state.hidden); document.body.classList.toggle("hide", state.hidden); return render(); }
  if (d.act === "prev" || d.act === "next") { const m = ymShift(state.month, d.act === "prev" ? -1 : 1); if (m <= ymNow) { state.month = m; render(); } return; }
  if (d.flow) { state.flow = d.flow; return render(); }
  if (d.clearcat !== undefined) { state.category = null; return render(); }
  if (d.filter && !d.go) { state.filter = d.filter; state.category = null; return render(); }
  if (d.go) return go(d.go, { filter: d.filter, cat: d.cat });
});
document.addEventListener("input", (ev) => {
  if (ev.target.id !== "q") return;
  clearTimeout(searchTimer);
  searchTimer = setTimeout(async () => { state.q = ev.target.value; const pos = ev.target.selectionStart; await render(); const i = document.getElementById("q"); i.focus(); i.setSelectionRange(pos, pos); }, 250);
});
document.addEventListener("change", (ev) => { if (ev.target.id === "file" && ev.target.files.length) upload([...ev.target.files]); });
document.addEventListener("dragover", (ev) => { if (document.getElementById("drop")) ev.preventDefault(); });
document.addEventListener("drop", (ev) => { if (document.getElementById("drop")) { ev.preventDefault(); upload([...ev.dataTransfer.files]); } });
document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") closeSheet(); });

(async () => {
  try {
    state.months = await api("/months");
    if (state.months.length && !state.months.includes(state.month)) state.month = state.months[0];  // abre no último mês com dados
  } catch { state.months = []; }
  render();
})();
