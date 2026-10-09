# Finanças

App pessoal: importa o CSV de conta do Nubank, categoriza por regras suas e mostra gastos por categoria no mês.

## Rodar (um comando)
```bash
export FINANCAS_OWN_NAMES="SEU NOME COMPLETO"   # contas suas, separadas por ";" (opcional)
./run.sh                                         # abre http://localhost:8000
./run.sh import extrato.csv fatura.csv          # importa sem abrir a tela
```
Na primeira execução as regras padrão já são carregadas.

### Para desenvolver
```bash
pip install -e ".[dev]"
uvicorn financas.api:app --reload      # http://localhost:8000
pytest
```
Dados ficam em `financas.db` (SQLite, ignorado pelo git; mude com `FINANCAS_DB`).

## Interface
Mobile-first, tema escuro, em `src/financas/static/` (HTML/CSS/JS puros, sem build). Telas: **Início**, **Atividades**
(busca, filtros e categorização por toque), **Gastos** (acumulado do mês vs. anterior e rosca por categoria),
**Fluxo** (entradas e gastos por dia) e **Importar**. O olho no topo oculta os valores. No celular, "Adicionar à tela
inicial" instala como app (PWA). Inspirada em apps de finanças; sem marcas ou logos de terceiros.

## Como funciona
- `POST /import` — importa o CSV de conta ou de fatura (detecta pelo cabeçalho). Reimportar é seguro: linhas já vistas são ignoradas
  (chave = identificador + valor + descrição + contador; o ID do Nubank sozinho **não** é único).
- `POST /rules/seed` — carrega as regras padrão (`default_rules.json`: Transporte, Delivery, Saúde...); `DELETE /rules/{id}` apaga uma.
- `POST /rules` — `{"pattern": "uber", "category": "Transporte", "priority": 0}`. Maior prioridade vence;
  empate vai para o padrão mais longo.
- `PUT /own-names/{nome}` — nome (como aparece no Pix) das suas outras contas; essas transferências não são gasto.
- `PATCH /transactions/{id}` — categoria manual (`{"category": "Família", "remember": true}`); fica travada e `remember` cria uma regra pela contraparte.
- `GET /reports/monthly?month=2026-09` — gastos por categoria.

## O que NÃO conta como gasto
`transfer` (entre contas suas), `card_payment` (pagamento de fatura; o gasto real está na fatura),
`credit_funding` (entrada fictícia do Pix no crédito; o Pix de saída conta como gasto) e
`passthrough` (recebeu e repassou o mesmo valor no mesmo dia).

## Dados reais
`samples/` está no `.gitignore`: extratos reais têm nomes, CPFs parciais e contas. Testes usam `tests/fixtures/`.

## Próximos passos
Parcelas futuras (falta uma fatura com parcelamento para validar o formato) → patrimônio manual → Open Finance.
