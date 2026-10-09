# ADR 0009 — Interface em JS puro, mobile-first, instalável

- **Status:** Proposto — aguarda revisão do Thiago
- **Data:** 2026-10-09
- **Fase:** 2 — Interface
- **Decidido por:** Claude, por delegação do Thiago ("tome as melhores decisões"); **aguarda revisão do Thiago**

## Contexto

O dono quer uma interface de celular no estilo dos apps de finanças atuais e rodar tudo com um comando. Um front com build (Node, bundler, framework) adicionaria dependência e uma segunda linguagem a um projeto que é Python.

## Decisão

HTML, CSS e JavaScript puros em `src/financas/static/`, servidos pelo próprio FastAPI; **sem build**. Gráficos em SVG escritos à mão (linha acumulada, rosca, barras). Manifesto para instalar como app. Tema escuro. Tudo que vem do CSV passa por `esc()` antes de entrar no HTML.

## Consequências

- `./run.sh` basta; nada para compilar.
- Sem framework, o arquivo `app.js` cresce: se passar de algumas centenas de linhas por tela, separar em módulos antes de adotar framework.
- Ícones são emojis (simples, mas variam por aparelho). Ícone do app é SVG; o iPhone prefere PNG (pendência).
- A interface foi inspirada em apps de finanças existentes, sem copiar marca, logo ou ícones de terceiros.
