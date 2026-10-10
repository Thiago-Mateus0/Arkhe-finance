# Spec — Interface

Mobile-first, sem build. Código em `src/financas/static/`. O "porquê" está nos ADRs 0009, 0010 e 0014.

## Telas

| Tela | O que mostra |
|---|---|
| **Início** | Gastos do mês com gráfico acumulado; aviso de pendentes; três maiores categorias; cartão Orçamento (os três mais pressionados); transações recentes; saldo (receitas − gastos) e gasto no cartão |
| **Atividades** | Busca; filtros Todas, Entradas, Saídas, Sem categoria, Cartão, Não contam; lançamentos agrupados por dia (Hoje, Ontem, dia da semana, data) |
| **Gastos** | Gasto acumulado do mês contra o mês anterior (linha tracejada), com valor por dia ao tocar; rosca e lista de categorias; tabela de valores por dia |
| **Orçamento** | Resumo do mês (orçado e gasto nas categorias), um item por categoria com barra, estado e quanto resta ou passou; botão para criar; tocar num item edita ou remove (ver `orcamento.md`) |
| **Fluxo** | Receitas e gastos por dia (Geral, Entradas, Saídas) e saldo do mês |
| **Importar** | Escolher ou arrastar vários CSV; resultado por arquivo |

## Navegação e temas

- **Celular:** barra de abas com rótulos (Início, Atividades, Gastos, Orçamento, Fluxo, Importar), fixa embaixo; cabe em telas de 320 px sem cortar texto nem rolar para o lado.
- **Computador (a partir de 900 px):** menu lateral com a marca; conteúdo centralizado; no Início, cartões em duas colunas.
- **Tema:** escuro por padrão. Um botão (sol/lua) no topo alterna entre escuro e claro; a escolha fica guardada no navegador e é aplicada antes de desenhar a tela, para não piscar.

## Comportamentos

- **Ao abrir, o app mostra o mês mais recente que tem lançamentos** (se o mês atual está vazio), e não um mês em branco.
- Mês sem lançamentos explica o que fazer; sem nenhum lançamento no banco, manda para a aba Importar.
- Seletor de mês em todas as telas; não avança além do mês atual.
- Tocar numa transação abre a folha de categoria (com "lembrar" marcado por padrão).
- O olho no topo oculta todos os valores (preferência guardada no navegador; se o navegador não guardar, segue sem lembrar).
- Erros de carregamento mostram a mensagem e um botão para tentar de novo.
- Instalável como app ("Adicionar à tela inicial").

## Acessibilidade

Sinal explícito (+ / −) além da cor; rosca e gráficos com `aria-label`; tabela de valores por dia como alternativa ao gráfico; respeita `prefers-reduced-motion`.
