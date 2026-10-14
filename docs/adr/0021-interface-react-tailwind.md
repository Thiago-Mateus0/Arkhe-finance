# ADR 0021 — Interface em React + Tailwind, com cartões e navegação flutuante

- **Status:** Proposto
- **Data:** 2026-10-14
- **Fase:** 2 — Design (reaberta por este ADR)
- **Decidido por:** Thiago pediu uma interface "mais tecnológica" ("dashboard bonito, tela bonita, sofisticada, com interações") e aprovou o protótipo em `docs/prototipo/interface-celular.html`; a escolha de stack e o guia por tela foram propostos por Claude e **aguardam o aceite do Thiago**
- **Revoga:** [ADR 0009](0009-interface-sem-build.md) (JS puro, sem build, gráficos em SVG à mão) e, do [ADR 0014](0014-identidade-visual-e-temas.md), a parte de **navegação** e de **layout de computador**

## Contexto

O front atual é HTML, CSS e JS puros, sem build (ADR 0009). Ele funciona e cobre o uso real, mas o dono quer um nível maior de acabamento e de interação: movimento, gaveta de detalhes, gráfico que se toca, números que contam. Isso é possível em JS puro, mas cada peça é escrita à mão e o `app.js` já é o maior arquivo do front. O ecossistema React + Tailwind tem componentes e padrões prontos para esse tipo de interface (o dono achou referências no catálogo 21st.dev).

A referência visual foi um app de finanças comercial que o Thiago usa, mostrado por capturas de tela dele. As capturas têm dado real e **não** entram no repositório. O protótipo foi escrito do zero, com dados fictícios.

## Decisão

**Front novo em React + TypeScript + Vite + Tailwind**, em `web/`, falando com a API que já existe. O backend não muda (FastAPI, SQLite, ADR 0001 e 0008).

| Dependência | Para quê |
|---|---|
| `react`, `react-dom` | Componentes e estado da tela |
| `typescript` | Os tipos protegem o centavo inteiro e o contrato da API |
| `vite`, `@vitejs/plugin-react` | Servidor de desenvolvimento e build |
| `tailwindcss` | Estilo por tokens, os mesmos dos temas |
| `vitest` | Testa a formatação de centavos para reais, a única "conta" do front |

**Fora, de propósito:** biblioteca de gráfico (os gráficos continuam em SVG próprio, como no protótipo) e biblioteca de animação (CSS cobre o protótipo; só entra uma se algo concreto pedir, com justificativa).

**Regras que continuam valendo:** dinheiro é centavo inteiro e vira reais só na borda (ADR 0011); tudo que vem do CSV é não confiável. O React escapa texto por padrão, e `dangerouslySetInnerHTML` fica proibido no projeto (regra 8 do CLAUDE.md).

**Migração tela a tela.** O front atual continua servido enquanto o novo cresce; começa pelo Início. Quando a última tela migrar, `src/financas/static/` sai. Cada tela é uma PR.

### Visual

- **Fundo escuro e uma aurora de cor no topo** da home, que some no preto. Cartões de vidro com cantos grandes e borda fina; um tom de cor por cartão.
- **Hierarquia só por tamanho:** rótulo cinza pequeno, valor grande em negrito, linha de apoio cinza.
- **Navegação flutuante em pílula** na base, com botão redondo "+" ao lado e uma barra de importar acima dela. Substitui a barra de abas com rótulos do ADR 0014.
- **Movimento com função:** números contam até o valor, o gráfico se desenha, cartões entram em sequência, gaveta sobe da base e se fecha arrastando. Tudo respeita `prefers-reduced-motion`.
- **Cor de destaque:** o ciano do ADR 0014 continua. Os cartões usam tons de fundo próprios.
- **Sem IA, sem plano pago, sem mascote.** O campo de "perguntar" que existe no app de referência não entra; no lugar dele fica "Importar extrato ou fatura".

### Guia por tela

| Tela | O que o protótipo mostra e a tela real deve ter |
|---|---|
| **Início** | Saudação sobre a aurora; abas Contas, Cartão e Patrimônio; carrossel da fatura; avisos (pendentes, orçamento estourado ou perto do limite); grade de cartões (fluxo de caixa, assinaturas, orçamento em anel, parcelas a vir); gráfico acumulado que se toca; barra segmentada de categorias; transações recentes |
| **Atividades** | Busca; filtros Todos, Gastos, Receitas, Pendentes (com contagem); lançamentos agrupados por dia; tocar abre a gaveta de categoria, com "lembrar para sempre" |
| **Orçamento** | Resumo do mês e um cartão por categoria com barra e estado; tocar abre a gaveta para ajustar o limite |
| **Seletor de mês** | Botão no topo da home abre a lista de meses; todas as telas acompanham |
| **Olho** | Borra todos os valores |
| **Gastos, Fluxo, Regras, Importar** | **Ainda sem desenho.** Mantêm o comportamento do `docs/spec/interface.md` e ganham o visual novo quando migrarem (pendência P16) |
| **Computador (900 px ou mais)** | **Ainda sem desenho** (P16). Vale o menu lateral do ADR 0014 até haver um novo |

## Consequências

- **Esta decisão volta a um padrão que o ADR 0014 tirou de propósito.** O 0014 existe porque a primeira interface ficou parecida com um app comercial no clima (escuro, menu flutuante em pílula, botão "+", lista por dia). O protótipo aprovado traz de volta a pílula e o "+". O que mantém identidade própria: o ciano no lugar do verde-limão, a aurora, a marca, o nome, e a ausência de IA e de plano pago. O Thiago já viu e aprovou o protótipo, mas o risco de "parecer com o Pierre" fica registrado aqui para o portfólio.
- **O protótipo usa cores de categoria provisórias**, e uma delas é o próprio ciano de destaque. Isso contradiz o 0014 ("o destaque nunca marca uma categoria") e a paleta validada do ADR 0010. **A implementação real usa a paleta do 0010**, e o protótipo não é referência de cor de categoria.
- **Contraste a refazer.** O 0014 verificou contraste sobre fundos lisos. Texto sobre a aurora e sobre cartões de vidro precisa de nova verificação (saudação, valores, rótulos cinza). Isso é critério de aceite de cada tela migrada.
- **Tema claro continua exigido** pelo 0014 e não existe no protótipo. A implementação define todas as cores como tokens para os dois temas desde o início; a escolha do usuário continua guardada no navegador e não segue o sistema.
- **Tela cheia no celular, moldura só no computador:** o protótipo preenche a tela do aparelho; a moldura de celular que aparece no computador é só de demonstração.
- **Build passa a existir.** A CI ganha `npm ci`, checagem de tipos, `vitest` e `vite build`, e perde o `node --check` do `app.js` quando ele sair. O `./run.sh` precisa continuar sendo suficiente (pendência P15).
- **PWA:** o manifesto e o ícone passam a sair do build; o ícone em PNG para o iPhone (P10) entra junto.
- **Documentos a atualizar quando este ADR for aceito:** `CLAUDE.md` (linha "Front" da stack, comandos, "Onde está o quê"), `README.md`, `docs/spec/interface.md` (o "sem build" do cabeçalho) e a nota de status do ADR 0009 e do 0014 para "Revogado". Nada disso é editado antes do aceite.
- **Licença:** nenhum componente do catálogo 21st.dev é copiado sem conferir a licença do autor; o protótipo não copia código de ninguém.
