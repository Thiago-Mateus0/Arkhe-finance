/** Curva suave que passa pelos pontos (Catmull-Rom convertida em Bézier). */
export function suave(p: readonly (readonly [number, number])[]): string {
  if (p.length === 0) return "";
  let d = `M${p[0]![0].toFixed(1)} ${p[0]![1].toFixed(1)}`;
  for (let i = 0; i < p.length - 1; i++) {
    const p0 = p[i - 1] ?? p[i]!, p1 = p[i]!, p2 = p[i + 1]!, p3 = p[i + 2] ?? p2;
    d += ` C${(p1[0] + (p2[0] - p0[0]) / 6).toFixed(1)} ${(p1[1] + (p2[1] - p0[1]) / 6).toFixed(1)},` +
      `${(p2[0] - (p3[0] - p1[0]) / 6).toFixed(1)} ${(p2[1] - (p3[1] - p1[1]) / 6).toFixed(1)},${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;
  }
  return d;
}

/** Soma acumulada de n posições; dia sem valor conta zero. */
export function acumulado(valores: readonly number[], n: number): number[] {
  let s = 0;
  return Array.from({ length: n }, (_, i) => (s += valores[i] ?? 0));
}
