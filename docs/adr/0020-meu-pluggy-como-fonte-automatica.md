# ADR 0020 — Meu Pluggy como fonte automática de lançamentos

- **Status:** Aceito
- **Data:** 2026-10-14
- **Fase:** 6 — Automático e compartilhado
- **Decidido por:** Thiago ("prefiro usar o Meu Pluggy, para ver dia a dia")

## Contexto

O ADR 0002 escolheu CSV primeiro e Open Finance depois, atrás da mesma camada de importação. A pendência P8 perguntava qual agregador e qual o custo. Para uso **pessoal**, o Meu Pluggy dá acesso gratuito, sem prazo, à API do próprio titular, com limite de conexões de contas do mesmo titular. Os planos de produção para apps de terceiros são pagos e fora de escala para este projeto. Acesso direto ao Open Finance, sem intermediário, exige ser instituição autorizada.

## Decisão

A fonte automática será o **Meu Pluggy**, como **um importador novo** que entrega lançamentos no mesmo formato interno que o CSV, passando pela mesma classificação, regras e deduplicação. O CSV continua suportado.

## Consequências

- Complementa o ADR 0002; não o revoga.
- **Os dados bancários passam por uma empresa terceira** (a Pluggy). A frase do README "sem entregar acesso à conta a terceiros" deixa de valer quando isto for implementado e deve ser atualizada junto.
- As credenciais da API ficam só na máquina do dono (variável de ambiente ou arquivo ignorado pelo git), nunca no repositório (regra 1 e ADR 0007).
- **"Tempo real" não é a expectativa certa:** relatos de uso indicam que o Meu Pluggy atualiza os itens cerca de uma vez por dia e não permite forçar. A frequência real precisa ser confirmada na conta do dono (P14). A promessa é "atualizado todo dia", não "na hora".
- Webhook da Pluggy não alcança um app em `localhost`; a sincronização seria por consulta periódica (polling) do app.
- Chave de duplicata: lançamentos vindos do Pluggy precisam casar com os já importados por CSV, para não duplicar. Exige um caso real e teste antes de implementar.
- Quem mais usar o app (P9) precisaria da própria conta no Meu Pluggy.
