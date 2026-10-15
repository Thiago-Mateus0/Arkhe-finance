import { useState, type FormEvent } from "react";
import { sb } from "../lib/supabase";

export function Login() {
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [entrando, setEntrando] = useState(false);

  const entrar = async (e: FormEvent) => {
    e.preventDefault();
    if (!sb) return;
    setEntrando(true); setErro(null);
    const { error } = await sb.auth.signInWithPassword({ email: email.trim(), password: senha });
    if (error) setErro("E-mail ou senha incorretos.");
    setEntrando(false);
  };

  return (
    <main className="page login">
      <h1>Arkhe Finance</h1>
      <p className="t2">Entre para ver suas finanças.</p>
      <form onSubmit={entrar} className="pilha">
        <label className="campo" htmlFor="lemail">E-mail</label>
        <input id="lemail" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <label className="campo" htmlFor="lsenha">Senha</label>
        <input id="lsenha" type="password" autoComplete="current-password" required value={senha} onChange={(e) => setSenha(e.target.value)} />
        {erro && <p className="neg" role="alert">{erro}</p>}
        <button type="submit" className="btn" disabled={entrando}>{entrando ? "Entrando…" : "Entrar"}</button>
      </form>
    </main>
  );
}
