# ADR 0014 — Identidade visual própria, tema claro opcional e layout de computador

- **Status:** Aceito
- **Data:** 2026-10-09
- **Fase:** 2 — Design
- **Decidido por:** Thiago pediu (identidade própria, tema claro opcional, computador); a cor, a marca e a navegação foram escolhidas por Claude e **aguardam revisão do Thiago**

## Contexto

A primeira interface (ADR 0009) foi inspirada em um app de finanças existente e acabou parecida com ele no clima: tema escuro, destaque em verde-limão, menu flutuante em pílula com botão "+" e lista por dia. Como o projeto também é portfólio, ele precisa ter identidade própria. Além disso, o Thiago quer poder usar no computador e escolher o tema.

## Decisão

- **Cor de destaque:** ciano — `#22d3ee` no escuro, `#0e7490` no claro. Aparece só em linhas, aba ativa e botão principal; as categorias seguem a paleta do ADR 0010.
- **Marca:** três barras crescentes sobre quadrado arredondado na cor de destaque (logo, ícone do app e favicon). Nome mantido: "Finanças".
- **Navegação:** barra de abas **com rótulos** no celular; **menu lateral** no computador. O botão flutuante "+" deixa de existir: "Importar" é uma aba.
- **Tema claro opcional:** o padrão continua escuro. Um botão no topo alterna e a escolha fica guardada no navegador (se ele não guardar, segue sem lembrar). Não segue a configuração do sistema, de propósito: a escolha é do usuário.
- **Computador (a partir de 900 px):** menu lateral, conteúdo centralizado e, no Início, cartões em duas colunas.

## Consequências

- **Contraste verificado:** nos dois temas, texto, destaque e valores positivos e negativos passam de 4,5:1 sobre o cartão e sobre o fundo.
- **Paleta de categorias no claro** (a do ADR 0010, passos claros) passou em todas as verificações de cor, mas três cores ficam abaixo de 3:1 sobre o cartão claro. O alívio exigido está cumprido: a lista de categorias nomeia cada fatia e há tabela de valores por dia.
- A cor de destaque não faz parte da paleta de categorias e não foi validada como par categórico; por isso ela só marca elementos de interface, nunca uma categoria.
- O nome "Finanças" é genérico (pendência P11). A identidade visual é própria; o nome ainda não.
