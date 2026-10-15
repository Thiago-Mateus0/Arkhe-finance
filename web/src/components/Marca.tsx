// Logo "pedra-chave" (geometria em scripts/gerar_logo.py). As cores vêm do tema (styles.css).
export function Marca({ tam = 34 }: { tam?: number }) {
  return (
    <svg viewBox="0 0 100 84.9" width={tam} height={tam * 0.849} aria-hidden="true" focusable="false">
      <defs><mask id="mkf" maskUnits="userSpaceOnUse" x="0" y="0" width="100" height="84.9"><rect width="100" height="53.8" fill="#fff"/><g stroke="#000" strokeWidth="3.4"><line x1="50.0" y1="55.5" x2="-22.63" y2="2.35"/><line x1="50.0" y1="62.0" x2="26.25" y2="-24.81"/><line x1="50.0" y1="62.0" x2="73.75" y2="-24.81"/><line x1="50.0" y1="55.5" x2="122.63" y2="2.35"/></g></mask></defs><g mask="url(#mkf)"><path fill="var(--logo-roxo)" d="M0.97 59.79A50 50 0 0 1 7.19 24.17L28.65 39.87A26.7 26.7 0 0 0 23.37 57.83Z"/><path fill="var(--logo-roxo)" d="M92.81 24.17A50 50 0 0 1 99.03 59.79L76.63 57.83A26.7 26.7 0 0 0 71.35 39.87Z"/><path fill="var(--logo-azul)" d="M7.19 24.17A50 50 0 0 1 33.78 2.70L41.41 30.62A26.7 26.7 0 0 0 28.65 39.87Z"/><path fill="var(--logo-azul)" d="M66.22 2.70A50 50 0 0 1 92.81 24.17L71.35 39.87A26.7 26.7 0 0 0 58.59 30.62Z"/><path fill="var(--logo-chave)" d="M33.78 2.70A50 50 0 0 1 66.22 2.70L58.59 30.62A26.7 26.7 0 0 0 41.41 30.62Z"/></g><rect x="0" y="57.2" width="23.3" height="27.7" fill="var(--logo-roxo)"/><rect x="76.7" y="57.2" width="23.3" height="27.7" fill="var(--logo-roxo)"/>
    </svg>
  );
}
