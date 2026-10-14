import { describe, expect, it } from "vitest";
import { acumulado, suave } from "./grafico";

describe("gráfico", () => {
  it("acumula em centavos inteiros e completa os dias que faltam com zero", () => {
    expect(acumulado([100, 0, 250], 5)).toEqual([100, 100, 350, 350, 350]);
    expect(acumulado([], 3)).toEqual([0, 0, 0]);
  });
  it("curva passa pelo primeiro e pelo último ponto", () => {
    const d = suave([[0, 10], [5, 20], [10, 5]]);
    expect(d.startsWith("M0.0 10.0")).toBe(true);
    expect(d.endsWith("10.0 5.0")).toBe(true);
    expect(suave([])).toBe("");
  });
});
