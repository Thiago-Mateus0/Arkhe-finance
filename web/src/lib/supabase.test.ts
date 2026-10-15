import { describe, expect, it } from "vitest";
import { origemDoSupabase } from "./supabase";

describe("origemDoSupabase", () => {
  it("tira o caminho e a barra que quebram o login", () => {
    expect(origemDoSupabase("https://abc.supabase.co/rest/v1/")).toBe("https://abc.supabase.co");
    expect(origemDoSupabase("https://abc.supabase.co/")).toBe("https://abc.supabase.co");
    expect(origemDoSupabase("  https://abc.supabase.co  ")).toBe("https://abc.supabase.co");
  });
  it("não quebra com texto que não é URL", () => {
    expect(origemDoSupabase("abc")).toBe("abc");
  });
});
