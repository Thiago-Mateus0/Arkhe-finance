# Spec — Interface

Mobile-first. Código em `web/` (React, ADR 0021). O "porquê" está nos ADRs 0010, 0014 e 0021. O protótipo que originou o visual está em `docs/prototipo/interface-celular.html`.

## Telas

| Tela | O que mostra |
|---|---|
| **Início** | Saudação sobre a aurora; abas **Contas** e **Cartão**. Contas: carrossel (gasto no cartão e parcelas já comprometidas), avisos (lançamentos sem categoria; orçamento estourou ou perto do limite), fluxo de caixa, assinaturas do mês, orçamento usado, parcelas a vir, gasto acumulado (tocar ou arrastar mostra o valor até o dia), barra de gastos por categoria e transações recentes. Cartão: gasto no cartão e parcelas a vir. A aba Patrimônio entra com a fase 5 |
| **Atividades** | Busca; filtros Todas, Entradas, Saídas, Sem categoria, Cartão, Não contam; lançamentos agrupados por dia (Hoje, Ontem, dia da semana, data); tocar abre a gaveta de categoria |
| **Regras de categoria** | Aberta por um botão em Atividades (não é aba). Lista de regras por categoria; tocar abre a folha para editar ou apagar; botão Nova regra |
| **Gastos** | Gasto acumulado do mês contra o mês anterior (linha tracejada), com valor por dia ao tocar; rosca e lista de categorias; tabela de valores por dia |
| **Orçamento** | Resumo do mês (orçado e gasto nas categorias), um item por categoria com barra, estado e quanto resta ou passou; botão para criar; tocar num item edita ou remove (ver `orcamento.md`) |
| **Fluxo** | Receitas e gastos por dia (Geral, Entradas, Saídas) e saldo do mês |
| **Importar** | Escolher ou arrastar vários CSV; resultado por arquivo |

## Navegação e temas

- **Celular:** pílula flutuante na base (Início, Atividades, Gastos, Orçamento, Fluxo) e um botão `+` que abre Importar; na Início há ainda a barra "Importar extrato ou fatura". Regras de categoria abre por um botão em Atividades.
- **Computador (a partir de 900 px):** menu lateral com a marca e todas as telas, conteúdo centralizado de até 920 px e as gavetas no centro da tela.
- **Tema:** escuro por padrão. Um botão (sol/lua) no topo alterna entre escuro e claro; a escolha fica guardada no navegador e é aplicada antes de desenhar a tela, para não piscar. Não segue a configuração do sistema, de propósito (ADR 0014).

## Comportamentos

- **Ao abrir, o app mostra o mês mais recente que tem lançamentos** (se o mês atual está vazio), e não um mês em branco.
- Mês sem lançamentos explica o que fazer; sem nenhum lançamento no banco, manda para a aba Importar.
- Seletor de mês (gaveta com a lista de meses) no topo das telas; não avança além do mês atual.
- Tocar numa transação abre a gaveta de categoria (com "lembrar" marcado por padrão). Confirmações de apagar (regra, orçamento) acontecem na própria gaveta, sem janela do navegador. Gavetas fecham com Escape, tocando fora ou arrastando a alça para baixo.
- O olho no topo oculta todos os valores (preferência guardada no navegador; se o navegador não guardar, segue sem lembrar).
- Erros de carregamento mostram a mensagem e um botão para tentar de novo.
- Instalável como app ("Adicionar à tela inicial").

## Acessibilidade

Sinal explícito (+ / −) além da cor; rosca e gráficos com `aria-label`; tabela de valores por dia como alternativa ao gráfico; respeita `prefers-reduced-motion`.
