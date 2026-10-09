# ADR 0001 — Stack: Python, FastAPI e SQLite local

- **Status:** Aceito
- **Data:** 2026-10-06
- **Fase:** 1 — Fundação
- **Decidido por:** Thiago

## Contexto

Projeto de uso pessoal, possivelmente compartilhado com mais uma pessoa depois. Não há orçamento de infraestrutura e os dados são financeiros: um servidor de terceiros seria custo e risco sem benefício na primeira versão. O dono prefere Python.

## Decisão

Backend em **Python + FastAPI**, banco **SQLite** em arquivo local (`financas.db`, ou o caminho de `FINANCAS_DB`), acesso pela biblioteca padrão `sqlite3`. O dado roda e fica na máquina do dono.

## Consequências

- Custo de manter: zero. Backup é copiar o arquivo do banco.
- Todo acesso ao banco passa por `db.py` e `service.py`, sem SQL espalhado pela interface; trocar por Postgres depois não obriga a reescrever a API (ADR 0008).
- Sem ORM de propósito: o esquema é pequeno e o SQL é legível.
