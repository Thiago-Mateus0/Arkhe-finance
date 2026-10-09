# Spec — Interface

Mobile-first, tema escuro, sem build. Código em `src/financas/static/`. O "porquê" está nos ADRs 0009 e 0010.

## Telas

| Tela | O que mostra |
|---|---|
| **Início** | Gastos do mês com gráfico acumulado; aviso de pendentes; três maiores categorias; transações recentes; saldo (receitas − gastos) e gasto no cartão |
| **Atividades** | Busca; filtros Todas, Entradas, Saídas, Sem categoria, Cartão, Não contam; lançamentos agrupados por dia (Hoje, Ontem, dia da semana, data) |
| **Gastos** | Gasto acumulado do mês contra o mês anterior (linha tracejada), com valor por dia ao tocar; rosca e lista de categorias; tabela de valores por dia |
| **Fluxo** | Receitas e gastos por dia (Geral, Entradas, Saídas) e saldo do mês |
| **Importar** | Escolher ou arrastar vários CSV; resultado por arquivo |

## Comportamentos

- Seletor de mês em todas as telas; não avança além do mês atual.
- Tocar numa transação abre a folha de categoria (com "lembrar" marcado por padrão).
- O olho no topo oculta todos os valores (preferência guardada no navegador; se o navegador não guardar, segue sem lembrar).
- Erros de carregamento mostram a mensagem e um botão para tentar de novo.
- Instalável como app ("Adicionar à tela inicial").

## Acessibilidade

Sinal explícito (+ / −) além da cor; rosca e gráficos com `aria-label`; tabela de valores por dia como alternativa ao gráfico; respeita `prefers-reduced-motion`.
