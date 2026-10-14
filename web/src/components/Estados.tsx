export function Erro({ msg, onTentar }: { msg: string; onTentar: () => void }) {
  return (
    <div className="card alert a-neg" role="alert">
      <div className="ic2">!</div>
      <div><b>Não deu para carregar</b><small>{msg}</small></div>
      <button type="button" className="tab" onClick={onTentar} style={{ marginLeft: "auto" }}>Tentar de novo</button>
    </div>
  );
}
export const Carregando = () => <p className="empty" role="status">Carregando…</p>;
export const Vazio = ({ children }: { children: React.ReactNode }) => <p className="empty">{children}</p>;
