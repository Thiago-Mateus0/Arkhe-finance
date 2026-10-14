import { describe, expect, it } from "vitest";
import { hrefDe, lerHash } from "./rotas";

describe("rotas", () => {
  it("lê rota e parâmetros", () => {
    const l = lerHash("#/atividades?cat=Delivery&f=uncat");
    expect(l.rota).toBe("atividades");
    expect(l.params.get("cat")).toBe("Delivery");
    expect(l.params.get("f")).toBe("uncat");
  });
  it("rota desconhecida ou vazia cai no início", () => {
    expect(lerHash("").rota).toBe("inicio");
    expect(lerHash("#/qualquer").rota).toBe("inicio");
  });
  it("monta o href e ignora parâmetro vazio", () => {
    expect(hrefDe("atividades", { cat: "Saúde", q: "" })).toBe("#/atividades?cat=Sa%C3%BAde");
    expect(hrefDe("gastos")).toBe("#/gastos");
  });
});
