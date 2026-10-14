# Pendências e status

Este arquivo guarda duas coisas que **não** são spec: o **status** do projeto (fases) e o que **falta decidir**. Spec diz o que o sistema faz; ADR diz por quê.

## Onde estamos

O projeto segue as mesmas quatro etapas do Lifetrailer. Aqui elas se misturaram no começo (conversamos e já codamos, e a documentação veio depois), por isso a tabela diz **o que cada etapa cobriu**, não uma ordem rígida.

| Etapa | Estado | O que cobre | Onde está |
|---|---|---|---|
| **Levantamento** | ✅ fechado | Quem usa, CSV antes de Open Finance, bancos, objetivo, o que fica para depois | ADRs 0001, 0002, 0006, 0008, 0012, 0013 |
| **Arquitetura** | ✅ fechado | Stack, o que conta como gasto, chave de duplicata, repasse, dinheiro em centavos | Specs `importacao`, `classificacao`, `categorias`, `relatorios`; ADRs 0003 a 0005 e 0011 |
| **Design** | ✅ fechado | Telas, cores por categoria, identidade própria, tema claro opcional, layout de computador. Interface em React + Tailwind aplicada ([ADR 0021](adr/0021-interface-react-tailwind.md)); a aba Patrimônio entra com a fase 5 | Spec `interface`; ADRs 0010, 0014, 0021 (o 0009 foi revogado) |
| **Código** | 🟡 em andamento | Importador, classificação, regras, relatórios, telas, orçamento, parcelas e assinaturas prontos; uso real (fase 3) e controle (fase 4) concluídos. Falta patrimônio (fase 5) e o automático (fase 6) | `src/`, `tests/` |

**Numeração antiga das fases** (usada nos ADRs, que não se editam depois de aceitos): 0 e 1 = Levantamento e Arquitetura; 2 = Design; 3 em diante = Código. Fase 3 (uso real) é a etapa de código em que você usa o app e aponta o que falta.

### Fases do código (numeração dos ADRs)

| Fase | Objetivo | Estado |
|---|---|---|
| 3 · Uso real | Rodar no dia a dia, importar vários meses, corrigir o que incomodar | ✅ concluída: meses fechados, o que sobrou sem categoria fica |
| 4 · Controle | Orçamento por categoria, assinaturas, parcelas futuras, tela de regras | ✅ concluída |
| 5 · Patrimônio | Saldos e investimentos informados à mão, metas, exportação e backup | aguardando (nada decidido ainda; ver P7) |
| 6a · Fonte automática | Meu Pluggy como importador (ADR 0020), **antecipada para agora por decisão do Thiago** | **em andamento**: falta P14 (conta dele) |
| 6 · Compartilhado | Login, hospedagem, uso por duas pessoas | aguardando |

**Critério para sair da fase 3:** o dono fecha um mês inteiro sem pendência e confia nos números.

## Decisões abertas

| # | Pendência | Bloqueia | Recomendação |
|---|---|---|---|
| P1 | ~~Como o Nubank escreve compra parcelada na fatura?~~ — respondido: uma linha por parcela, "TÍTULO - Parcela N/M" (no Pix no crédito, "- N/M") | — | Feito; implementado como "Parcelas a vir" (ADR 0012) |
| ~~P2~~ | ~~Orçamento: limite mensal fixo ou por mês? O que dispara o aviso?~~ | — | ✅ proposto no [ADR 0015](adr/0015-orcamento-por-categoria.md): fixo, aviso a 80% e ao estourar (aguarda revisão) |
| P12 | Orçamento: limite diferente por mês (sazonalidade)? Aviso fora da tela (notificação)? | Fase 4 | Só se o uso mostrar necessidade |
| P3 | ~~Pix no crédito contado duas vezes~~ — resolvido: para o dono é transferência (ADR 0017); para terceiro conta uma vez, pela fatura (ADR 0018) | — | Feito. Atenção: depende da fatura estar importada |
| P4 | Categorias criadas pelo usuário não têm cor própria (só 8 têm). Como atribuir cor a categorias livres? | Fase 4 | Atribuir da paleta, por ordem de criação, e guardar |
| P5 | ~~Detectar assinaturas~~ — decidido: assinatura é a categoria "Assinaturas", marcada por regra (ADR 0019); sem detecção automática | — | Feito. Sugestão automática (3+ meses, valor parecido) fica como ideia futura, só se o uso pedir |
| P6 | ~~Tela para editar e apagar regras~~ — feita: *Regras de categoria*, dentro de Atividades | — | Feito |
| P7 | Saldo das contas: lembrete mensal para o dono informar? | Fase 5 | Aviso na tela Início, no dia 1 |
| P8 | ~~Open Finance: qual agregador e custo?~~ — decidido: **Meu Pluggy** (gratuito para uso pessoal), como importador novo (ADR 0020) | — | Feito; implementação é a fase 6 |
| P9 | Compartilhar com mais uma pessoa: login, onde hospedar, como proteger a API | Fase 6 | Proposto no [ADR 0024](adr/0024-hospedagem-com-login.md): rede privada + identidade na borda, falhando fechado. **A API atual não pode ser exposta** (ADR 0008) |
| P20 | Hospedagem: a outra pessoa vê **os mesmos lançamentos** (mesma casa) ou **só os dela** (casas separadas)? | ADR 0024 | Fato e decisão do Thiago; o modelo (`household_id`) aceita os dois |
| P21 | Hospedagem: aceita **dado real num servidor de terceiro**, ou só em casa atrás de rede privada? E a outra pessoa concorda com os dados dela no sistema? | ADR 0024 | Recomendação: começar em casa, atrás de rede privada; servidor só se precisar estar no ar sem o computador |
| P10 | Ícone do app em PNG para o iPhone | Fase 3 | Gerar o PNG quando o dono instalar no celular |
| P14 | Meu Pluggy: com que frequência a conta do dono atualiza o Nubank (relatos dizem cerca de uma vez por dia), o conector traz conta **e** cartão, e qual o formato dos lançamentos? | Fase 6 | O Thiago cria a conta no Meu Pluggy, conecta o Nubank e confere na tela deles. Fato que só ele tem; **as credenciais nunca vão para o chat nem para o git** |
| P13 | E-mail dos commits: parte do histórico usa um endereço pessoal visível no repositório público, e a configuração do git local tem um erro de digitação no domínio (os commits não ligam ao perfil do GitHub) | Antes de divulgar | Usar o e-mail `noreply` do GitHub nos próximos commits (`git config user.email`). **Não reescrever o histórico** do repositório público sem decisão do Thiago |
| P17 | ~~Cartão: mês da fatura ou da compra?~~ — decidido: **mês da fatura** (ADR 0022), igual ao CSV | — | Feito. A data da compra fica guardada para uma tela futura |
| P18 | ~~Resgate de aplicação (RDB) contava como receita, e a aplicação como gasto~~ — decidido: tipo **investimento**, fora de gasto e receita (ADR 0023) | — | Feito |
| P19 | Pix no crédito vindo do Pluggy: conta e fatura não trazem o identificador comum que o CSV tem, então o pareamento do ADR 0018 (por identificador) não vale para linhas do Pluggy | Fase 6a | Parear por mesmo dia e valor oposto, com teste das leituras; precisa de caso real e do Thiago. Enquanto isso, essas linhas seguem como gasto na conta e na fatura |
| P11 | ~~Nome do app~~ — decidido: **Arkhe Finance** (ADR 0016) | — | Feito; capturas de tela refeitas com `scripts/capturas.py` |
| P15 | ~~Como o `./run.sh` serve o front em React?~~ — decidido no aceite do ADR 0021: `./run.sh` faz o build quando `web/dist` não existe ou está velho, e o FastAPI serve `web/dist` | — | Feito na PR do scaffold |
| P16 | ~~Telas sem desenho no visual novo (Gastos, Fluxo, Regras, Importar, computador)~~ — feitas na migração, no mesmo visual do protótipo, e conferidas no navegador | — | Feito (ADR 0021) |

## Antes de divulgar como portfólio

- [ ] O Thiago revisa e ajusta `docs/processo-de-trabalho.md` para refletir como ele realmente trabalha.
- [x] O Thiago revisou e aceitou os ADRs que estavam **Propostos** (0003, 0004, 0005, 0007, 0009, 0010, 0011, 0014).
- [x] O Thiago aceitou o ADR **0015** (orçamento) em 2026-10-14.
- [x] Histórico do git conferido: nenhum extrato, nome de terceiro, CPF ou arquivo de banco em nenhum commit (ver P13 sobre o e-mail dos commits).
- [x] P13: decidido em 2026-10-14 pela recomendação; commits novos usam o e-mail `noreply` do GitHub (histórico não reescrito).
- [x] Hospedagem: o Thiago escolheu **Supabase + Cloudflare Pages**, como o Lifetrailer, e casas separadas ([ADR 0025](adr/0025-supabase-como-backend-hospedado.md), que substitui o 0024). Etapas 1 a 6 abertas, um PR cada; a migração do banco real é feita por ele. Até a virada, o app continua local, em `127.0.0.1`.
- [x] O Thiago aceitou o ADR **0021** (interface em React + Tailwind) em 2026-10-14.
