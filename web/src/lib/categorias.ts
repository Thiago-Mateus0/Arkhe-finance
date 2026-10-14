// Cor por categoria: fixa, da paleta validada do ADR 0010 (nunca por ranking, nunca o ciano de destaque).
const COR: Record<string, number> = {
  "Transporte": 1, "Delivery": 2, "Mercado": 3, "Alimentação": 4, "Saúde": 5, "Educação": 6, "Moradia": 7, "Compras": 8,
};
export const corDaCategoria = (nome: string): string => `var(--c${COR[nome] ?? 0})`;
export const temCorPropria = (nome: string): boolean => (COR[nome] ?? 0) > 0;
export const SEM_CATEGORIA = "Sem categoria";

/** Tipos de lançamento que não contam como gasto nem receita (explicação para o dono). */
export const KIND: Record<string, string> = {
  expense: "Gasto", income: "Receita",
  transfer: "Transferência entre contas suas (não conta como gasto)",
  card_payment: "Pagamento de fatura (o gasto está na fatura)",
  credit_funding: "Pix no crédito (o gasto é o Pix de saída)",
  passthrough: "Repasse: entrou e saiu o mesmo valor (não conta)",
};
export const contaComoValor = (kind: string): boolean => kind === "expense" || kind === "income";
