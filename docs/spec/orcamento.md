# Spec — Orçamento

Um limite de gasto por categoria. O "porquê" está no ADR 0015. Dinheiro em centavos no banco; reais só na API e na tela (ADR 0011).

## Orçamento

Um orçamento é `categoria` + `limite` mensal. O **mesmo limite vale todos os meses**: não há limite diferente por mês. Há no máximo um orçamento por categoria; definir de novo troca o limite.

- A categoria não pode ser `Sem categoria` (classifique antes de orçar) nem vazia, nem passar de 60 caracteres.
- O limite é maior que zero e tem no máximo 2 casas decimais. Valor inválido é recusado (HTTP 422), sem gravar nada.
- Remover um orçamento não apaga nenhum lançamento.

## Gasto contra o limite

O gasto de uma categoria no mês é a soma dos lançamentos do tipo `gasto` dessa categoria (ver `classificacao.md`). Estorno reduz o gasto. Receita, repasse, transferência e pagamento de fatura não entram. O mês é o do lançamento.

## Estado

| Estado | Quando | Rótulo na tela |
|---|---|---|
| `ok` | gasto abaixo de 80% do limite | Dentro do limite |
| `atencao` | gasto de 80% do limite até **exatamente** o limite | Atenção |
| `estourou` | gasto **maior** que o limite | Estourou |

Os limites são comparados em centavos inteiros, sem arredondamento: 80% é `gasto × 5 ≥ limite × 4`. Gastar exatamente o limite é `atencao`, não `estourou`.

Cada item traz: `categoria`, `limite`, `gasto`, `restante` (pode ser negativo), `percentual` (uma casa decimal, arredondado para cima no meio, em inteiros; só exibição, o estado nunca depende dele) e `estado`. A resposta traz também `orcado_total` e `gasto_nas_categorias`. Os itens vêm do mais grave para o mais folgado (estourou, atenção, ok) e, dentro do estado, do maior percentual para o menor. Uma categoria orçada sem gasto no mês aparece com gasto zero.

## Pontos de entrada

`GET /budgets?month=aaaa-mm` · `PUT /budgets/{categoria}` com `{"limite": 150.5}` · `DELETE /budgets/{categoria}` · `python -m financas orcamento "Delivery" 150,50`.

## Tela

Cartão **Orçamento** no Início (os três mais pressionados) e tela **Orçamento** (aba própria): resumo, um item por categoria com barra e rótulo, folha para criar, editar e remover.
