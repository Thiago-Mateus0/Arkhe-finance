# Spec — Importação

O que o sistema faz ao receber um CSV. O "porquê" está nos ADRs 0002, 0003 e 0011.

## Formatos aceitos

| Formato | Cabeçalho | Data | Valor |
|---|---|---|---|
| Conta Nubank | `Data,Valor,Identificador,Descrição` | `dd/mm/aaaa` | decimal com ponto; saída negativa, entrada positiva |
| Fatura Nubank | `date,title,amount` | `aaaa-mm-dd` | decimal com vírgula; compra positiva, pagamento/estorno negativo |

O formato é detectado pelo cabeçalho. Qualquer outro cabeçalho é recusado com erro legível (HTTP 422 na API, mensagem no terminal), sem gravar nada.

## Sinal e unidade

Internamente, **saída é negativa e entrada positiva**, em centavos inteiros. Na fatura, a compra (positiva no CSV) é gravada como saída; o pagamento e o estorno (negativos no CSV) são gravados como entrada.

## Idempotência

Cada linha recebe uma **chave de duplicata**. Reimportar o mesmo arquivo, ou um arquivo que se sobrepõe a outro, grava apenas as linhas novas. A resposta informa quantas linhas foram lidas, novas e duplicadas.

- **Conta:** identificador + valor + descrição + contador de ocorrência (o identificador do banco não é único).
- **Fatura:** data + valor + título + contador de ocorrência (não há identificador). Duas compras idênticas no mesmo dia são duas compras.

## Contraparte

Nas linhas de Pix da conta, o nome de quem enviou ou recebeu é extraído da descrição (maiúsculas, espaços normalizados). Na fatura, a contraparte é o título da compra.

## Depois de gravar

Toda importação reclassifica as linhas da conta (ver `classificacao.md`), porque repasse e transferência dependem do conjunto inteiro, não de uma linha.

## Pontos de entrada

`POST /import` (um arquivo por chamada) · `python -m financas import arq1.csv arq2.csv` · tela **Importar** (vários arquivos, arrastar e soltar).

## Meu Pluggy (fonte automática)

`python -m financas pluggy` (ou `./run.sh pluggy`) lê conta e cartão pela API do Meu Pluggy e grava pelo mesmo caminho do CSV (ADRs 0020 e 0022). Credenciais em `.env` ou variáveis de ambiente: `PLUGGY_CLIENT_ID`, `PLUGGY_CLIENT_SECRET`, `PLUGGY_ITEM_ID`. O `.env` é ignorado pelo git; há um `.env.example` sem valores.

- **Só lançamento `POSTED`.** Pendente é contado à parte e não entra.
- **Direção pelo `type`** (`DEBIT` sai, `CREDIT` entra), nunca pelo sinal do valor: no cartão o sinal vem invertido.
- **Cartão:** a data é a de lançamento na fatura (`billPostDate`), igual ao CSV. Parcela vira o sufixo "- Parcela n/m" no texto, que o resto do app já lê.
- **Pagamento de fatura** (`PAGAMENTO_FATURA`) é `card_payment`.
- **Sem contar em dobro com o CSV, nos dois sentidos:** uma linha de outra origem, mesma conta, mesmo valor com sinal e data até 1 dia de diferença, é o mesmo lançamento. Vale um para um, e a data exata tem preferência. Reimportar qualquer fonte não muda nada.
- **Linha malformada** (data, valor ou tipo inválido) é ignorada e contada, sem quebrar a sincronização.
- A resposta informa lidas, novas, já existentes, pendentes e ignoradas.
- Fora de escopo por enquanto (P19): pareamento de Pix no crédito entre conta e fatura para linhas do Pluggy, que não trazem o identificador comum do CSV.

