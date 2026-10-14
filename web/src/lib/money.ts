// Dinheiro é centavo inteiro (ADR 0011). A API entrega reais como número; isso vira centavo
// aqui, na borda, e daqui em diante só se soma inteiro.
export const toCents = (reais: number): number => Math.round(reais * 100);

const milhar = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });

/** Formata centavos como "R$ 1.234,56". `sign` mostra "+" nos positivos; negativos sempre levam "−". */
export function brl(cents: number, sign = false): string {
  const abs = Math.abs(Math.trunc(cents));
  const inteiro = Math.trunc(abs / 100);
  const resto = String(abs % 100).padStart(2, "0");
  const prefixo = cents < 0 ? "− " : sign && cents > 0 ? "+ " : "";
  return `${prefixo}R$ ${milhar.format(inteiro)},${resto}`;
}
