const D = {
  olho: "M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12zM12 9a3 3 0 100 6 3 3 0 000-6z",
  olhoFechado: "M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12zM12 9a3 3 0 100 6 3 3 0 000-6zM4 4l16 16",
  baixo: "M6 9l6 6 6-6",
  voltar: "M15 6l-6 6 6 6",
  casa: "M3 11l9-8 9 8M5 10v10h14V10",
  lista: "M4 6h16M4 12h16M4 18h10",
  pizza: "M12 3a9 9 0 109 9h-9zM15 3.5A9 9 0 0120.5 9H15z",
  alvo: "M12 3a9 9 0 100 18 9 9 0 000-18zM12 12V3M12 12l6.5 4.5",
  fluxo: "M7 4v14M3 14l4 4 4-4M17 20V6M13 10l4-4 4 4",
  enviar: "M12 15V4M7 9l5-5 5 5M5 20h14",
  mais: "M12 5v14M5 12h14",
  sol: "M12 8a4 4 0 100 8 4 4 0 000-8zM12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4",
  lua: "M20 14.5A8.5 8.5 0 019.5 4a8.5 8.5 0 1010.5 10.5z",
  busca: "M11 4a7 7 0 100 14 7 7 0 000-14zM20 20l-3.5-3.5",
  fechar: "M6 6l12 12M18 6L6 18",
  repetir: "M17 2l4 4-4 4M3 11V9a3 3 0 013-3h15M7 22l-4-4 4-4M21 13v2a3 3 0 01-3 3H3",
  parcelas: "M4 7h16M4 12h10M4 17h6",
  regras: "M4 6h10M4 12h16M4 18h7M17 4l3 2-3 2",
} as const;
export type NomeIcone = keyof typeof D;

export function Icone({ nome, tam = 21 }: { nome: NomeIcone; tam?: number }) {
  return (
    <svg className="ico" width={tam} height={tam} viewBox="0 0 24 24" aria-hidden="true"><path d={D[nome]} /></svg>
  );
}
