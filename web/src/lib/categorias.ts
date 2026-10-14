// Cor por categoria: fixa, da paleta validada do ADR 0010 (nunca por ranking, nunca o ciano de destaque).
const COR: Record<string, number> = {
  "Transporte": 1, "Delivery": 2, "Mercado": 3, "Alimentação": 4, "Saúde": 5, "Educação": 6, "Moradia": 7, "Compras": 8,
};
export const corDaCategoria = (nome: string): string => `var(--c${COR[nome] ?? 0})`;
export const SEM_CATEGORIA = "Sem categoria";
