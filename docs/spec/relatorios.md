# Spec — Relatórios

Tudo é calculado sobre `gasto` e `receita` (ver `classificacao.md`). Valores saem do banco em centavos e chegam à API em reais.

## Mensal — `GET /reports/monthly?month=aaaa-mm`

| Campo | Significado |
|---|---|
| `gastos_total`, `receitas_total` | somas do mês |
| `gastos_mes_anterior` | soma de gastos do mês anterior (inteiro) |
| `gastos_cartao`, `gastos_conta` | gastos do mês por origem (fatura / conta) |
| `por_categoria[]` | `categoria`, `valor`, `qtd`, `mes_anterior`; ordenado do maior para o menor valor |

## Diário — `GET /reports/daily?month=aaaa-mm`

`dias[]` (um item por dia do mês, com `gastos` e `entradas`) e `anterior[]` (gastos por dia do mês anterior). O mês anterior de janeiro é dezembro do ano anterior; fevereiro de ano bissexto tem 29 dias.

## Transações — `GET /transactions`

Filtros: `month` (obrigatório), `category`, `kind` ou `kinds` (lista separada por vírgula), `q` (busca em descrição e contraparte, sem diferenciar maiúsculas; vazio é ignorado), `desc=true` (mais recentes primeiro).

## Meses com dados — `GET /months`

Lista `aaaa-mm` dos meses que têm algum lançamento, do mais recente para o mais antigo. A tela usa para abrir no último mês com dados.

## Comparação com o mês anterior

A tela compara o gasto acumulado até o **mesmo dia** do mês anterior, não o total do mês anterior inteiro; num mês fechado, os dois coincidem.
