// Mesmas chaves do app antigo (valores em JSON). Se o navegador não guarda, segue sem lembrar.
export function lerPref<T>(chave: string, padrao: T): T {
  try {
    const v = localStorage.getItem(chave);
    return v === null ? padrao : (JSON.parse(v) as T);
  } catch {
    return padrao;
  }
}
export function gravarPref(chave: string, valor: unknown): void {
  try { localStorage.setItem(chave, JSON.stringify(valor)); } catch { /* sem storage */ }
}
