# ADR 0015 — Orçamento: limite mensal fixo por categoria, aviso a 80% e ao estourar

- **Status:** Proposto — aguarda revisão do Thiago
- **Data:** 2026-10-10
- **Fase:** 4 — Controle
- **Decidido por:** Claude, por delegação do Thiago ("vamos aplicar tudo"); a pendência P2 trazia esta recomendação; **aguarda revisão do Thiago**

## Contexto

Ver para onde o dinheiro foi (fases anteriores) não basta para controlá-lo: o Thiago quer saber, durante o mês, quanto ainda pode gastar em cada categoria. A pendência P2 deixou em aberto duas perguntas: o limite é fixo ou muda por mês, e o que dispara o aviso.

## Decisão

- **Limite mensal fixo por categoria:** um valor que vale todos os meses, definido uma vez.
- **Aviso em dois níveis:** *atenção* a partir de 80% do limite (inclusive) e *estourou* só quando o gasto passa do limite. Gastar exatamente o limite é atenção, não estouro.
- **Só gasto conta**, o mesmo tipo de lançamento dos relatórios (ADR 0004): repasse, transferência e pagamento de fatura ficam de fora; estorno reduz.
- **Não se orça `Sem categoria`:** o limite de algo que ninguém classificou não diz nada.
- A comparação é em **centavos inteiros** (ADR 0011).

## Consequências

- Simples de entender e de usar: um limite por categoria e três estados. A leitura "estourou" é só acima do limite; quem preferir que 100% já seja estouro revoga este ADR.
- Mês com gasto sazonal (por exemplo, presentes em dezembro) não cabe em limite fixo; limite por mês fica como evolução, se o uso mostrar necessidade (`docs/pendencias.md`).
- O orçamento é por nome de categoria: renomear uma categoria nas regras deixa o orçamento antigo apontando para um nome sem gasto. Aceitável hoje, porque categorias não são renomeadas pelo app.
- O estado fica na tela, sem notificação: o app só avisa quando é aberto.
