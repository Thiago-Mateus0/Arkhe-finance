# Arkhe Finance

App pessoal de finanças: importa o CSV de conta e de fatura do Nubank, classifica cada lançamento, categoriza por regras e mostra para onde o dinheiro vai. Roda **local** (SQLite), com interface web pensada para celular. Um projeto solo, que resolve uma necessidade real e também serve de portfólio.

**Onde estamos:** Levantamento, Arquitetura e Design fechados (interface em React, ADR 0021); **Código**: uso real (fase 3) e controle (fase 4) concluídos, com a fase 5 (patrimônio) como próxima. Não reabra decisão de etapa anterior sem ADR. O quadro completo está em `docs/pendencias.md`.

Pessoa: **Thiago** (dono, decide produto e regra de dinheiro; não é obrigado a ler código — vê o resultado e o PR).

---

## Stack

| Camada | Escolha |
|---|---|
| Backend | Python 3.11+ · FastAPI · SQLite (stdlib `sqlite3`) — ADR 0001 |
| Dados | CSV do Nubank hoje; Open Finance depois, atrás da mesma camada de importação — ADR 0002 |
| Front | React + TypeScript + Vite + Tailwind em `web/`, mobile-first, instalável (PWA) — ADR 0021. O FastAPI serve `web/dist` |
| Testes | pytest · vitest (front) · Playwright só para capturas de tela |

---

## Regras invioláveis

1. **Dado financeiro real nunca entra no git.** O repositório é **público**. Extratos reais ficam em `samples/` (ignorado). Testes e demonstração usam só dados fictícios (`tests/fixtures/`, `data/demo/`). — ADR 0007
2. **Dinheiro é centavo inteiro** no banco e no código; vira reais só na borda (API/tela). Nunca `float` para somar. — ADR 0011
3. **Número vem do dado, nunca do texto.** Contagem, soma e porcentagem saem do banco ou da fixture na hora; não escreva valor literal em doc, issue ou teste de comportamento.
4. **ADR aceito não se edita.** Decisão nova revoga a antiga com ADR novo apontando para o anterior. Se sua saída contradiz um ADR, sinalize — não sobrescreva em silêncio.
5. **Regra que mexe em dinheiro só entra com teste** das leituras possíveis dela (o que conta como gasto, repasse, duplicata). Dez testes da mesma leitura errada não provam nada.
6. **Lacuna de domínio não vira improviso.** O que não está decidido vai para `docs/pendencias.md`.
7. **Vocabulário em português**, como nos specs: gasto, receita, repasse, transferência, fatura, categoria, pendente. Não traduza nem invente sinônimo.
8. **Tudo que vem do CSV é não confiável:** passa por `esc()` antes de entrar em HTML.
9. **Importar é idempotente.** Reimportar o mesmo arquivo não muda nada.

---

## Onde está o quê

```
docs/spec/*.md        ← o que o sistema faz, por área. Sem "porquê".
docs/adr/*.md         ← por que decidi assim. Uma decisão por arquivo.
docs/pendencias.md    ← o que falta decidir, por fase. Também guarda o status do projeto.
docs/processo-de-trabalho.md ← como o projeto é construído (inclui o uso de IA).
docs/agents/          ← config das skills (issue tracker, docs de domínio).
src/financas/         ← código: importer, classifier, rules, service, parcelas, assinaturas, api
web/                  ← front (React); `npm run build` gera web/dist, que o FastAPI serve
data/demo/            ← CSVs 100% fictícios (gerados por scripts/gerar_demo.py)
samples/              ← extratos REAIS. Ignorado pelo git. Nunca commitar.
tests/                ← pytest; fixtures fictícias em tests/fixtures/
```

**Antes de mexer numa área:** leia o spec dela e os ADRs que a tocam.

---

## Comandos

```bash
pip install -e ".[dev]"
python -m pytest -q                         # toda a suíte
./run.sh                                    # app em http://localhost:8000
./run.sh import extrato.csv fatura.csv      # importa sem abrir a tela
./run.sh backup [--dir PASTA] [--manter N]  # cópia conferida do banco real (nunca no git)
./run.sh restaurar ARQUIVO [--sim]          # volta o banco para um backup
./run.sh pluggy                             # sincroniza com o Meu Pluggy (credenciais no .env)
./run.sh demo                               # app com dados fictícios e orçamentos de exemplo (demo.db)
python -m financas orcamento "Delivery" 150,50   # limite mensal de uma categoria
python scripts/gerar_demo.py                # regenera data/demo/ (determinístico)
pip install -e ".[capturas]" && python scripts/capturas.py   # refaz docs/img/ com a demo (precisa do build)
(cd web && npm ci && npm run check && npm test && npm run build)   # front: tipos, testes e build
(cd web && npm run dev)                     # front com recarga (a API em :8000)
```

Nomes das suas outras contas (viram transferência, não gasto): `export FINANCAS_OWN_NAMES="NOME COMPLETO;OUTRO NOME"`.

---

## Estilo de trabalho

- **Não abstraia antes da hora.** Código no nível real do projeto, sem camada que não paga aluguel.
- **Teste antes** no que for classificação ou dinheiro. Bug real vira teste.
- **Uma coisa por vez.** Se a tarefa cresceu além do combinado, pare e mostre o plano.
- **Não crie doc novo** sem checar se o conteúdo pertence a um spec ou ADR existente.
- **O diff mora na PR, não no chat.** Toda PR segue `.github/pull_request_template.md`, com **"O que conferir"**: até 3 linhas que o Thiago valida sem ler código.
- **Interface:** verifique no navegador (Playwright) antes de dizer que ficou pronta; olhe a imagem.
- Sem dependência nova sem justificar em uma linha.

---

## Autonomia

O Claude vai até o PR sozinho (e o Thiago faz o merge) quando a suíte passa, em: correção de bug com teste que falha antes, refatoração sem mudança de comportamento, implementação do que um ADR **aceito** já decidiu, teste/script/doc de processo.

**Abre o PR e para, esperando o Thiago:**
- decisão nova de produto ou de domínio (vira ADR);
- mudança na regra de classificação (o que conta como gasto), em duplicata ou em repasse;
- qualquer coisa que toque dado real, acesso ou publicação (deploy, hospedagem, login);
- fato que só o Thiago tem (formato de um CSV novo, o que é uma transferência dele).

**Decisão pendente não trava o trabalho.** Registre em `docs/pendencias.md` com as opções e a recomendação; siga com o que não depende dela.

**Formato de resposta:** (1) o que mudou, 1–3 linhas · (2) link do PR · (3) testes · (4) o que precisa do Thiago, só se existir. Português, direto.

---

## Agent skills

### Issue tracker
Issues no GitHub Issues de `Thiago-Mateus0/finan-as`. Veja `docs/agents/issue-tracker.md`.

### Domain docs
Single-context: `docs/spec/` + `docs/adr/` na raiz. Veja `docs/agents/domain.md`.
