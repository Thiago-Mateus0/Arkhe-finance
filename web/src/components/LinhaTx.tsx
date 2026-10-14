import { corDaCategoria, contaComoValor } from "../lib/categorias";
import { diaCurto } from "../lib/datas";
import type { Tx } from "../lib/api";
import { brl } from "../lib/money";

export const nomeBonito = (t: Tx): string =>
  t.account === "nubank_conta" && t.counterparty
    ? t.counterparty.toLowerCase().replace(/(^|\s)\S/g, (c) => c.toUpperCase())
    : t.description;

const iniciais = (n: string) => n.split(/\s+/).slice(0, 2).map((p) => p[0] ?? "").join("").toUpperCase();

export function LinhaTx({ t, onAbrir, comData = true }: { t: Tx; onAbrir?: (t: Tx) => void; comData?: boolean }) {
  const conta = contaComoValor(t.kind);
  const entrada = t.amount_cents > 0;
  const nome = nomeBonito(t);
  const cartao = t.account === "nubank_fatura" ? " · Cartão" : "";
  const corpo = (
    <>
      <div className="ic" style={{ ["--cc" as string]: corDaCategoria(t.category) }}>{conta ? iniciais(nome) : "↔"}</div>
      <div className="t">
        <b>{nome}</b>
        <small>{comData ? `${diaCurto(t.date)} · ` : ""}{conta ? t.category : "Não conta"}{cartao}</small>
      </div>
      <span className={`n v ${!conta ? "muted" : entrada ? "pos" : ""}`}>{brl(t.amount_cents, true)}</span>
    </>
  );
  return onAbrir
    ? <button type="button" className="tx" onClick={() => onAbrir(t)}>{corpo}</button>
    : <div className="tx">{corpo}</div>;
}
