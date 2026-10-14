import { describe, expect, it } from "vitest";
import { parseValor } from "./valor";

describe("parseValor", () => {
  it("aceita as formas que o dono digita", () => {
    expect(parseValor("150")).toBe(15000);
    expect(parseValor("150,5")).toBe(15050);
    expect(parseValor("1.500,00")).toBe(150000);
    expect(parseValor("R$ 99,90")).toBe(9990);
    expect(parseValor("1.500")).toBe(150000);
  });
  it("recusa o que não é um limite válido", () => {
    expect(parseValor("")).toBeNull();
    expect(parseValor("0")).toBeNull();
    expect(parseValor("-50")).toBeNull();
    expect(parseValor("abc")).toBeNull();
  });
  it("não arredonda em silêncio mais de 2 casas", () => {
    expect(parseValor("10,999")).toBeNull();
  });
});
