import { useRef, useState } from "react";
import { Cabecalho } from "../components/Cabecalho";
import { api, type ResultadoImport } from "../lib/api";
import { useApp } from "../lib/contexto";
import { sair } from "../lib/sessao";
import { NUVEM } from "../lib/supabase";

type Linha = { nome: string; ok: true; r: ResultadoImport } | { nome: string; ok: false; msg: string };

export function Importar() {
  const { invalidar, recarregarMeses, ir } = useApp();
  const entrada = useRef<HTMLInputElement>(null);
  const [linhas, setLinhas] = useState<Linha[]>([]);
  const [enviando, setEnviando] = useState(false);
  const [arrastando, setArrastando] = useState(false);

  const enviar = async (arquivos: File[]) => {
    if (arquivos.length === 0) return;
    setEnviando(true); setLinhas([]);
    const saida: Linha[] = [];
    for (const f of arquivos) {
      const fd = new FormData(); fd.append("file", f);
      try {
        const r = await api<ResultadoImport>("/import", { method: "POST", body: fd });
        saida.push({ nome: f.name, ok: true, r });
      } catch (e) {
        saida.push({ nome: f.name, ok: false, msg: (e as Error).message });
      }
      setLinhas([...saida]);
    }
    invalidar(); recarregarMeses(); setEnviando(false);
  };

  if (NUVEM) {
    return (
      <>
        <Cabecalho titulo="Importar" semMes />
        <p className="t2">Aqui você vê a versão na nuvem. A importação de CSV ainda é feita no computador:
          <code> python -m financas nuvem import arquivo.csv</code>. Depois é só abrir este app de novo.</p>
        <button type="button" className="btn" onClick={sair}>Sair</button>
      </>
    );
  }

  return (
    <>
      <Cabecalho titulo="Importar" semMes />
      <p className="t2">CSV da conta ou da fatura do Nubank. O app reconhece o tipo e ignora o que já foi importado.</p>
      <label className={`drop${arrastando ? " sobre" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setArrastando(true); }}
        onDragLeave={() => setArrastando(false)}
        onDrop={(e) => { e.preventDefault(); setArrastando(false); void enviar([...e.dataTransfer.files]); }}>
        <input ref={entrada} type="file" accept=".csv,text/csv" multiple hidden
          onChange={(e) => { void enviar([...(e.target.files ?? [])]); e.target.value = ""; }} />
        <b>{enviando ? "Importando…" : "Escolher arquivos CSV"}</b>
        <span className="sub">ou arraste e solte aqui</span>
      </label>
      <div className="pilha">
        {linhas.map((l) => (
          <div className="card" key={l.nome} role="status">
            <b>{l.nome}</b>
            {l.ok
              ? <p className="sub" style={{ whiteSpace: "normal" }}>{l.r.formato === "nubank_fatura" ? "Fatura do cartão" : "Conta"} · {l.r.novas} {l.r.novas === 1 ? "nova" : "novas"}, {l.r.duplicadas} já importadas</p>
              : <p className="neg" style={{ marginTop: 4 }}>{l.msg}</p>}
          </div>
        ))}
      </div>
      {linhas.length > 0 && !enviando && <button type="button" className="btn" onClick={() => ir("inicio")}>Ver resumo</button>}
    </>
  );
}
