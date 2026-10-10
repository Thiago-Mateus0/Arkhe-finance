# Spec — Categorias

O "porquê" está nos ADRs 0006 e 0010.

## Regras

Uma regra é `padrão` + `categoria` + `prioridade` (inteiro, padrão 0). O padrão é um trecho de texto, sem diferenciar maiúsculas, procurado em `descrição + contraparte`.

- Várias regras podem casar. Vence a de **maior prioridade**; em empate, a de **padrão mais longo** (mais específico).
- Nenhuma regra casa → categoria `Sem categoria` (**pendente**).
- Regras padrão vêm em `src/financas/default_rules.json` e são carregadas **uma vez**, na primeira vez que o banco é usado. Apagar uma regra padrão não a ressuscita.

## Categoria manual

Definir a categoria de uma transação a **trava**: nenhuma regra, nova ou antiga, a sobrescreve. A opção **lembrar** também cria uma regra pela contraparte (ou pela descrição, se não houver), com prioridade 5, e a aplica às outras transações não travadas.

## Cor e ícone

Cada categoria conhecida tem uma cor fixa (a cor segue a categoria, nunca a posição no ranking). Categorias sem cor própria — as definidas pelo usuário e as menos comuns — aparecem em cinza e, na rosca, agrupadas em "Outras categorias".

## Pontos de entrada

`POST /rules` · `POST /rules/seed` · `DELETE /rules/{id}` · `GET /rules` · `PATCH /transactions/{id}` · `GET /categories`.

## Gerenciar regras

Toda regra pode ser **criada, editada (padrão, categoria, prioridade) e apagada**, na tela *Regras de categoria* (acessada em Atividades) ou pela API (`POST`, `PUT` e `DELETE /rules`). Depois de qualquer mudança, as transações **não travadas** são recategorizadas. Padrão ou categoria vazios são recusados, porque um padrão vazio casaria com tudo.
