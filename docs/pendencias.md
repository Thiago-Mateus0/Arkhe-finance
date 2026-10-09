# Pendências e status

Este arquivo guarda duas coisas que **não** são spec: o **status** do projeto (fases) e o que **falta decidir**. Spec diz o que o sistema faz; ADR diz por quê.

## Fases

| Fase | Objetivo | Estado |
|---|---|---|
| 0 · Descoberta | Entender o problema, escolher stack e escopo | ✅ fechada (ADRs 0001, 0002, 0006, 0008) |
| 1 · Fundação | Importar CSV de conta e fatura, classificar, categorizar, relatório mensal | ✅ fechada (specs `importacao`, `classificacao`, `categorias`, `relatorios`) |
| 2 · Interface | Telas mobile-first, demonstração fictícia, documentação | ✅ fechada (spec `interface`, ADRs 0007, 0009, 0010) |
| **3 · Uso real** | Rodar no dia a dia, importar vários meses, corrigir o que incomodar | **em andamento** |
| 4 · Controle | Orçamento por categoria, assinaturas, parcelas futuras, tela de regras | aguardando a fase 3 |
| 5 · Patrimônio | Saldos e investimentos informados à mão, metas, exportação e backup | aguardando |
| 6 · Automático e compartilhado | Open Finance, login, hospedagem, uso por duas pessoas | aguardando |

**Critério para sair da fase 3:** o dono fecha um mês inteiro sem pendência e confia nos números.

## Decisões abertas

| # | Pendência | Bloqueia | Recomendação |
|---|---|---|---|
| P1 | Como o Nubank escreve compra parcelada na fatura? Falta um CSV de amostra (anonimizado) | Fase 4 (ADR 0012) | Aguardar uma fatura com parcelamento |
| P2 | Orçamento: limite por categoria é mensal fixo ou muda por mês? O que dispara o aviso (passou de X%, estourou)? | Fase 4 | Mensal fixo, aviso ao passar de 80% e ao estourar |
| P3 | Pix no crédito aparece na conta (Pix de saída) **e** pode aparecer na fatura. Contar uma vez só exige parear os dois | Fase 3 | Esperar um caso real nos dados antes de construir o pareamento |
| P4 | Categorias criadas pelo usuário não têm cor própria (só 8 têm). Como atribuir cor a categorias livres? | Fase 4 | Atribuir da paleta, por ordem de criação, e guardar |
| P5 | Detectar assinaturas (cobrança que se repete todo mês) | Fase 4 | Só depois de ter 3+ meses importados |
| P6 | Tela para editar e apagar regras (hoje só pela API) | Fase 4 | Lista simples dentro de Atividades |
| P7 | Saldo das contas: lembrete mensal para o dono informar? | Fase 5 | Aviso na tela Início, no dia 1 |
| P8 | Open Finance: qual agregador e qual o custo real? | Fase 6 | Pesquisar só quando chegar a fase 6 |
| P9 | Compartilhar com mais uma pessoa: login, onde hospedar, como proteger a API | Fase 6 | Hospedagem simples com login; **a API atual não pode ser exposta** (ADR 0008) |
| P10 | Ícone do app em PNG para o iPhone; tema claro | Fase 3 | Gerar o PNG quando o dono instalar no celular |

## Antes de divulgar como portfólio

- [ ] O Thiago revisa e ajusta `docs/processo-de-trabalho.md` para refletir como ele realmente trabalha.
- [ ] O Thiago revisa os ADRs marcados **Proposto** (0003, 0004, 0005, 0007, 0009, 0010, 0011) e muda o status para **Aceito** ou revoga com um ADR novo.
- [ ] Conferir o histórico do git por dado pessoal antes de tornar o repositório mais visível.
