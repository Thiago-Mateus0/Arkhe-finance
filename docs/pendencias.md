# Pendências e status

Este arquivo guarda duas coisas que **não** são spec: o **status** do projeto (fases) e o que **falta decidir**. Spec diz o que o sistema faz; ADR diz por quê.

## Onde estamos

O projeto segue as mesmas quatro etapas do Lifetrailer. Aqui elas se misturaram no começo (conversamos e já codamos, e a documentação veio depois), por isso a tabela diz **o que cada etapa cobriu**, não uma ordem rígida.

| Etapa | Estado | O que cobre | Onde está |
|---|---|---|---|
| **Levantamento** | ✅ fechado | Quem usa, CSV antes de Open Finance, bancos, objetivo, o que fica para depois | ADRs 0001, 0002, 0006, 0008, 0012, 0013 |
| **Arquitetura** | ✅ fechado | Stack, o que conta como gasto, chave de duplicata, repasse, dinheiro em centavos | Specs `importacao`, `classificacao`, `categorias`, `relatorios`; ADRs 0003 a 0005 e 0011 |
| **Design** | ✅ fechado | Telas, cores por categoria, identidade própria, tema claro opcional, layout de computador | Spec `interface`; ADRs 0009, 0010, 0014 |
| **Código** | 🟡 em andamento | Importador, classificação, regras, relatórios e telas prontos; uso real (fase 3) concluído. Falta o controle (fase 4 em diante) | `src/`, `tests/` |

**Numeração antiga das fases** (usada nos ADRs, que não se editam depois de aceitos): 0 e 1 = Levantamento e Arquitetura; 2 = Design; 3 em diante = Código. Fase 3 (uso real) é a etapa de código em que você usa o app e aponta o que falta.

### Fases do código (numeração dos ADRs)

| Fase | Objetivo | Estado |
|---|---|---|
| 3 · Uso real | Rodar no dia a dia, importar vários meses, corrigir o que incomodar | ✅ concluída: meses fechados, o que sobrou sem categoria fica |
| 4 · Controle | Orçamento por categoria ✅ (em revisão), assinaturas, parcelas futuras, tela de regras | **em andamento**: orçamento feito; o resto é o próximo |
| 5 · Patrimônio | Saldos e investimentos informados à mão, metas, exportação e backup | aguardando |
| 6 · Automático e compartilhado | Open Finance, login, hospedagem, uso por duas pessoas | aguardando |

**Critério para sair da fase 3:** o dono fecha um mês inteiro sem pendência e confia nos números.

## Decisões abertas

| # | Pendência | Bloqueia | Recomendação |
|---|---|---|---|
| P1 | Como o Nubank escreve compra parcelada na fatura? Falta um CSV de amostra (anonimizado) | Fase 4 (ADR 0012) | Aguardar uma fatura com parcelamento |
| ~~P2~~ | ~~Orçamento: limite mensal fixo ou por mês? O que dispara o aviso?~~ | — | ✅ proposto no [ADR 0015](adr/0015-orcamento-por-categoria.md): fixo, aviso a 80% e ao estourar (aguarda revisão) |
| P12 | Orçamento: limite diferente por mês (sazonalidade)? Aviso fora da tela (notificação)? | Fase 4 | Só se o uso mostrar necessidade |
| P3 | Pix no crédito aparece na conta (Pix de saída) **e** pode aparecer na fatura. Contar uma vez só exige parear os dois | Fase 3 | Esperar um caso real nos dados antes de construir o pareamento |
| P4 | Categorias criadas pelo usuário não têm cor própria (só 8 têm). Como atribuir cor a categorias livres? | Fase 4 | Atribuir da paleta, por ordem de criação, e guardar |
| P5 | Detectar assinaturas (cobrança que se repete todo mês) | Fase 4 | Só depois de ter 3+ meses importados |
| P6 | Tela para editar e apagar regras (hoje só pela API) | Fase 4 | Lista simples dentro de Atividades |
| P7 | Saldo das contas: lembrete mensal para o dono informar? | Fase 5 | Aviso na tela Início, no dia 1 |
| P8 | Open Finance: qual agregador e qual o custo real? | Fase 6 | Pesquisar só quando chegar a fase 6 |
| P9 | Compartilhar com mais uma pessoa: login, onde hospedar, como proteger a API | Fase 6 | Hospedagem simples com login; **a API atual não pode ser exposta** (ADR 0008) |
| P10 | Ícone do app em PNG para o iPhone | Fase 3 | Gerar o PNG quando o dono instalar no celular |
| P11 | Nome do app: "Finanças" é genérico; a identidade visual já é própria, o nome ainda não | Antes de divulgar | O Thiago escolhe; trocar é só texto e o logo |

## Antes de divulgar como portfólio

- [ ] O Thiago revisa e ajusta `docs/processo-de-trabalho.md` para refletir como ele realmente trabalha.
- [x] O Thiago revisou e aceitou os ADRs que estavam **Propostos** (0003, 0004, 0005, 0007, 0009, 0010, 0011, 0014).
- [ ] O Thiago revisa o ADR **0015** (orçamento), ainda **Proposto**, e muda o status para **Aceito** ou revoga com um ADR novo.
- [ ] Conferir o histórico do git por dado pessoal antes de tornar o repositório mais visível.
