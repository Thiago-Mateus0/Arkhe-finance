# Spec — Classificação

Cada lançamento tem um **tipo**. Só `gasto` entra no total de gastos; só `receita` entra no total de receitas. O "porquê" está nos ADRs 0004 e 0005.

## Tipos

| Tipo | O que é | Conta como |
|---|---|---|
| `expense` (gasto) | Saída de dinheiro para fora, ou compra no cartão | gasto |
| `income` (receita) | Entrada de dinheiro de fora | receita |
| `transfer` (transferência) | Pix de/para outra conta **do próprio dono**, inclusive o Pix no crédito (linha "Pix no Crédito - NOME" da fatura, com ou sem parcela) cujo NOME é dele | nada |
| `card_payment` (pagamento de fatura) | "Pagamento de fatura" na conta; "Pagamento recebido" na fatura | nada |
| `credit_funding` (Pix no crédito) | A entrada fictícia "Valor adicionado na conta por cartão de crédito" e, quando a fatura já tem a linha "Pix no Crédito - NOME" correspondente, o Pix de saída da conta | nada (o gasto é a linha da fatura) |
| `passthrough` (repasse) | Dinheiro que entrou e saiu sem ser do dono | nada |

## Regras, em ordem

1. Descrição começa com "Pagamento de fatura" (conta) ou "Pagamento recebido" (fatura) → `card_payment`.
2. Descrição começa com "Valor adicionado na conta por cartão de crédito" → `credit_funding`.
3. Contraparte está nos **nomes próprios** → `transfer`. Na fatura, a linha "Pix no Crédito - NOME" (aceita sufixo de parcela, "- 2/3") com NOME próprio também é `transfer`; com NOME de terceiro segue `gasto`. Os nomes vêm da variável `FINANCAS_OWN_NAMES` (separados por `;`) e da tabela `own_names` (`PUT /own-names/{nome}`).
4. Valor positivo → `income`; negativo → `expense`.
5. **Repasse, exato:** entrada e saída do mesmo valor no mesmo dia são pareadas, uma a uma.
6. **Repasse, por soma:** uma saída que ainda é `expense`, para uma contraparte que já teve repasse exato (um **condutor**), é pareada com um conjunto de até 4 entradas (`income`) de até 3 dias antes, cuja soma é exatamente o valor da saída. Entre as combinações possíveis, vale a mais recente; em empate, a de menos partes.

7. **Pix no crédito para terceiro, conta uma vez:** a saída da conta que tem entrada fictícia (mesmo identificador, valor oposto) é pareada com uma linha de fatura "Pix no Crédito - NOME" do mesmo nome, e vira `credit_funding`; o gasto fica na **fatura** (que traz o custo do crédito). O pareamento é por nome, **um para um**, com a saída até 45 dias antes da linha da fatura, e não por valor, porque a fatura é maior que o Pix. Entre várias saídas, vale a mais recente cujo valor não passa da linha da fatura (parcelado: só a data). Sem linha na fatura (ainda não importada), a saída segue `gasto`; parcelas seguintes da fatura seguem `gasto`.

Uma saída para contraparte que nunca foi condutora **nunca** é pareada por soma.

**Estorno na fatura:** linha de fatura com valor negativo que não é pagamento é `gasto` com valor positivo, e reduz o total de gastos.

## Quando a classificação roda

A cada importação e a cada mudança em `own_names`, sobre todas as linhas da conta e da fatura.

## Consulta

A tela **Atividades** mostra receitas e gastos por padrão; o filtro **Não contam** lista os demais tipos, com a explicação de cada um ao tocar na linha.
