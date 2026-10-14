import { useEffect, useRef, type ReactNode } from "react";

interface Props { aberta: boolean; titulo: string; onFechar: () => void; children: ReactNode }

/** Folha que sobe da base. Fecha com Escape, tocando fora ou arrastando a alça para baixo. */
export function Gaveta({ aberta, titulo, onFechar, children }: Props) {
  const folha = useRef<HTMLDivElement>(null);
  const y0 = useRef<number | null>(null);
  const dy = useRef(0);

  useEffect(() => {
    if (!aberta) return;
    const tecla = (e: KeyboardEvent) => { if (e.key === "Escape") onFechar(); };
    document.addEventListener("keydown", tecla);
    return () => document.removeEventListener("keydown", tecla);
  }, [aberta, onFechar]);

  const fim = () => {
    if (y0.current === null || !folha.current) return;
    y0.current = null;
    folha.current.style.transition = "";
    folha.current.style.transform = "";
    if (dy.current > 90) onFechar();
  };

  return (
    <div className={`sheet-wrap${aberta ? " on" : ""}`} onClick={onFechar} aria-hidden={!aberta}>
      <div ref={folha} className="sheet" role="dialog" aria-modal="true" aria-label={titulo} onClick={(e) => e.stopPropagation()}>
        <div className="grabarea"
          onPointerDown={(e) => { y0.current = e.clientY; dy.current = 0; if (folha.current) folha.current.style.transition = "none"; e.currentTarget.setPointerCapture(e.pointerId); }}
          onPointerMove={(e) => { if (y0.current === null || !folha.current) return; dy.current = Math.max(0, e.clientY - y0.current); folha.current.style.transform = `translateY(${dy.current}px)`; }}
          onPointerUp={fim} onPointerCancel={fim}>
          <div className="grab" />
        </div>
        {aberta && children}
      </div>
    </div>
  );
}
