/** "150", "150,5", "1.500,00", "R$ 99,90" -> centavos inteiros; inválido, zero ou negativo -> null.
 *  Mais de 2 casas é recusado em vez de arredondado em silêncio. */
export function parseValor(texto: string): number | null {
  if (/-/.test(texto)) return null;
  let t = texto.replace(/[^\d,.]/g, "");
  if (t.includes(",")) t = t.replace(/\./g, "").replace(",", ".");
  else if (/^\d{1,3}(\.\d{3})+$/.test(t)) t = t.replace(/\./g, ""); // 1.500 = mil e quinhentos
  if (/\.\d{3,}$/.test(t)) return null;
  const v = Number(t);
  return Number.isFinite(v) && v > 0 ? Math.round(v * 100) : null;
}
