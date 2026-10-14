import { describe, expect, it } from "vitest";
import { brl, toCents } from "./money";

describe("toCents", () => {
  it("converte reais da API em centavos inteiros", () => {
    expect(toCents(1182.75)).toBe(118275);
    expect(toCents(0)).toBe(0);
    expect(toCents(-39.9)).toBe(-3990);
  });
  it("não deixa o erro de ponto flutuante virar centavo", () => {
    expect(toCents(0.1 + 0.2)).toBe(30);
    expect(toCents(19.9 + 20)).toBe(3990);
  });
});

describe("brl", () => {
  it("formata com milhar e vírgula", () => {
    expect(brl(118275)).toBe("R$ 1.182,75");
    expect(brl(100000000)).toBe("R$ 1.000.000,00");
  });
  it("zero e centavos soltos", () => {
    expect(brl(0)).toBe("R$ 0,00");
    expect(brl(5)).toBe("R$ 0,05");
  });
  it("sinal explícito: negativo sempre, positivo só se pedido", () => {
    expect(brl(-3990)).toBe("− R$ 39,90");
    expect(brl(3990)).toBe("R$ 39,90");
    expect(brl(3990, true)).toBe("+ R$ 39,90");
    expect(brl(0, true)).toBe("R$ 0,00");
  });
});
