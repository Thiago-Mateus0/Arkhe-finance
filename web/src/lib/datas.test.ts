import { describe, expect, it } from "vitest";
import { mesCurto, nomeDoMes, rotuloDoDia, saudacao } from "./datas";

describe("datas", () => {
  it("nome do mês", () => {
    expect(nomeDoMes("2026-10")).toBe("Outubro 2026");
    expect(mesCurto("2026-03")).toBe("Mar 2026");
  });
  it("rótulo do dia: hoje, ontem e data", () => {
    const hoje = new Date(2026, 9, 14);
    expect(rotuloDoDia("2026-10-14", hoje)).toBe("Hoje");
    expect(rotuloDoDia("2026-10-13", hoje)).toBe("Ontem");
    expect(rotuloDoDia("2026-10-05", hoje)).toBe("5 out");
  });
  it("saudação", () => {
    expect(saudacao(8)).toBe("Bom dia");
    expect(saudacao(15)).toBe("Boa tarde");
    expect(saudacao(21)).toBe("Boa noite");
  });
});
