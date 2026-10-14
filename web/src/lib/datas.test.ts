import { describe, expect, it } from "vitest";
import { diaCurto, mesAtual, mesCurto, nomeDoMes, rotuloDoDia, saudacao, soMes } from "./datas";

describe("datas", () => {
  it("nomes do mês", () => {
    expect(nomeDoMes("2026-10")).toBe("Outubro 2026");
    expect(mesCurto("2026-03")).toBe("Mar 2026");
    expect(soMes("2026-05")).toBe("maio");
    expect(mesAtual(new Date(2026, 0, 5))).toBe("2026-01");
  });
  it("rótulo do dia: hoje, ontem, dia da semana e data", () => {
    const hoje = new Date(2026, 9, 14); // quarta-feira
    expect(rotuloDoDia("2026-10-14", hoje)).toBe("Hoje");
    expect(rotuloDoDia("2026-10-13", hoje)).toBe("Ontem");
    expect(rotuloDoDia("2026-10-11", hoje)).toBe("Domingo");
    expect(rotuloDoDia("2026-10-05", hoje)).toBe("5 de out");
    expect(diaCurto("2026-09-30")).toBe("30 de set");
  });
  it("saudação", () => {
    expect(saudacao(8)).toBe("Bom dia");
    expect(saudacao(15)).toBe("Boa tarde");
    expect(saudacao(21)).toBe("Boa noite");
  });
});
