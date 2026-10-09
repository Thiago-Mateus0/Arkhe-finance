# Finanças

App pessoal de finanças. Importa o **CSV de conta e de fatura do Nubank**, separa o que é gasto do que é só dinheiro passando pela conta, categoriza por regras e mostra, no celular, para onde o dinheiro está indo.

Nasceu de uma necessidade pessoal: ter visão do próprio dinheiro a partir do que o banco já exporta, sem entregar acesso à conta a terceiros. Roda **local** (SQLite), sem servidor e sem enviar dado financeiro a ninguém.

> **Onde estamos:** fase 3 — uso real. Detalhes em [`docs/pendencias.md`](docs/pendencias.md).

## Telas

Capturas em celular (390×844), com os dados fictícios de `data/demo/`.

<table>
<tr>
<td><img src="docs/img/inicio.png" width="230" alt="Início"><br><b>Início</b>: gastos do mês, pendentes e categorias</td>
<td><img src="docs/img/gastos.png" width="230" alt="Gastos"><br><b>Gastos</b>: acumulado contra o mês anterior</td>
<td><img src="docs/img/gastos-categorias.png" width="230" alt="Categorias"><br><b>Categorias</b>: rosca e lista</td>
</tr>
<tr>
<td><img src="docs/img/atividades.png" width="230" alt="Atividades"><br><b>Atividades</b>: busca, filtros, agrupado por dia</td>
<td><img src="docs/img/categorizar.png" width="230" alt="Categorizar"><br><b>Categorizar</b>: um toque, com "lembrar"</td>
<td><img src="docs/img/fluxo.png" width="230" alt="Fluxo"><br><b>Fluxo</b>: receitas e gastos por dia</td>
</tr>
</table>

## O problema que o app resolve

Somar tudo que saiu da conta dá um número errado. No extrato real:

- o **pagamento da fatura** repete gastos que já estão na fatura;
- um **Pix entre suas próprias contas** não é gasto nem receita;
- o **Pix no crédito** cria uma entrada que nunca foi dinheiro novo;
- **amigos mandam Pix e você repassa o mesmo valor** — dinheiro que só passou pela conta.

O app classifica cada lançamento em um tipo e só conta como gasto o que é gasto. Isso é o coração do projeto: [`docs/spec/classificacao.md`](docs/spec/classificacao.md).

## Como funciona

```
 CSV da conta ─┐                                ┌─ regras de categoria (+ manual que trava)
               ├─▶ importa ─▶ classifica ─▶ SQLite ─▶ relatórios ─▶ API FastAPI ─▶ app web (PWA)
 CSV da fatura ┘   (idempotente)  (tipo)      local     mensal/diário
```

- **Importar é idempotente:** reimportar, ou importar arquivos que se sobrepõem, não duplica nada.
- **Dinheiro em centavos inteiros**, nunca `float`.
- **Categoria manual trava:** nenhuma regra futura a sobrescreve.
- **Interface sem build:** HTML, CSS e JS puros, gráficos em SVG escritos à mão.

## Decisões de engenharia que valem uma olhada

| Tema | Onde ler |
|---|---|
| Chave de duplicata: o identificador do banco **não é único** | [ADR 0003](docs/adr/0003-chave-de-duplicata.md) |
| O que conta (e o que não conta) como gasto | [ADR 0004](docs/adr/0004-tipos-de-lancamento.md) |
| Repasse: pareamento exato e por soma, sem esconder gasto de verdade | [ADR 0005](docs/adr/0005-repasse.md) |
| Categorias por regras, em vez de IA enviando extrato a uma API | [ADR 0006](docs/adr/0006-categorias.md) |
| Repositório público, dados reais fora do git, demonstração fictícia | [ADR 0007](docs/adr/0007-dado-real-fora-do-git.md) |
| Interface sem build e cor fixa por categoria (paleta validada para daltonismo) | [ADR 0009](docs/adr/0009-interface-sem-build.md), [0010](docs/adr/0010-cor-por-categoria.md) |

Spec diz **o que** o sistema faz (`docs/spec/`); ADR diz **por quê** (`docs/adr/`). **ADR aceito não se edita:** decisão nova revoga a antiga com outro ADR.

## Testes

```bash
pip install -e ".[dev]"
python -m pytest -q
```

Cobrem o importador (os dois formatos), a classificação e o repasse, as regras de categoria, os relatórios, a API e os dados de demonstração. A CI roda a mesma suíte a cada PR.

## Rodando

Requer Python 3.11+.

```bash
./run.sh demo        # app com dados 100% fictícios em http://localhost:8000
```

Com os seus extratos:

```bash
export FINANCAS_OWN_NAMES="SEU NOME COMPLETO"      # suas outras contas (viram transferência)
./run.sh                                           # http://localhost:8000
./run.sh import extrato.csv fatura.csv             # ou use o botão + na tela
```

No celular, abra o endereço no navegador e use "Adicionar à tela inicial". Por enquanto a API **não tem login** e não deve ser exposta na internet (ADR 0008).

## Estrutura

```
src/financas/     importer · classifier · rules · service · api · static/ (front)
docs/spec/        o que o sistema faz, por área
docs/adr/         por que cada decisão foi tomada
docs/pendencias.md  fases e o que falta decidir
data/demo/        CSVs fictícios (gerados por scripts/gerar_demo.py)
tests/            pytest; fixtures fictícias
```

## Sobre os dados deste repositório

Todo dado aqui é **fictício**: nomes, empresas, CNPJ e valores da demonstração e dos testes foram inventados, no formato real do Nubank. Extratos reais ficam em `samples/`, que o git ignora.

## Como foi construído

Projeto solo, com apoio de um assistente de IA (Claude Code) na escrita de código e testes, sob specs e ADRs decididos pelo dono. O processo, sem enfeite, está em [`docs/processo-de-trabalho.md`](docs/processo-de-trabalho.md).
