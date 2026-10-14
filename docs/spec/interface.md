# Spec — Interface

Mobile-first. Código em `web/` (React, ADR 0021) e, nas telas ainda não migradas, em `src/financas/static/`. O "porquê" está nos ADRs 0010, 0014 e 0021. O desenho das telas novas está em `docs/prototipo/interface-celular.html`.

## Telas

| Tela | O que mostra |
|---|---|
| **Início** | Gastos do mês com gráfico acumulado; aviso de pendentes; três maiores categorias; cartão Orçamento (os três mais pressionados); transações recentes; saldo (receitas − gastos) e gasto no cartão |
| **Início**, card *Assinaturas* | Aparece só se há assinatura ativa: total do mês e até 3 itens com valor e a próxima cobrança estimada; tocar abre Atividades na categoria |
| **Início**, card *Parcelas a vir* | Aparece só se há parcelas restantes: até 3 meses, com total e quantidade de parcelas. É leitura da fatura, não entra nos gastos |
| **Atividades** | Busca; filtros Todas, Entradas, Saídas, Sem categoria, Cartão, Não contam; lançamentos agrupados por dia (Hoje, Ontem, dia da semana, data) |
| **Regras de categoria** | Aberta por um botão em Atividades (não é aba). Lista de regras por categoria; tocar abre a folha para editar ou apagar; botão Nova regra |
| **Gastos** | Gasto acumulado do mês contra o mês anterior (linha tracejada), com valor por dia ao tocar; rosca e lista de categorias; tabela de valores por dia |
| **Orçamento** | Resumo do mês (orçado e gasto nas categorias), um item por categoria com barra, estado e quanto resta ou passou; botão para criar; tocar num item edita ou remove (ver `orcamento.md`) |
| **Fluxo** | Receitas e gastos por dia (Geral, Entradas, Saídas) e saldo do mês |
| **Importar** | Escolher ou arrastar vários CSV; resultado por arquivo |

## Migração para o front novo (ADR 0021)

O **Início novo** está em `/novo`; as demais telas seguem no app antigo, em `/`, até migrarem. Mostra, para o mês escolhido: gasto no cartão e parcelas a vir (carrossel), avisos de lançamentos sem categoria e de orçamento (estourou ou perto do limite), fluxo de caixa, assinaturas, orçamento usado, parcelas a vir, gasto acumulado (tocar ou arrastar mostra o valor até o dia), barra de gastos por categoria e transações recentes. O olho oculta os valores (mesma preferência do app antigo). A aba Patrimônio entra com a fase 5.

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
