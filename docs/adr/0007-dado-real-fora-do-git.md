# ADR 0007 — Dado real fora do git; demonstração fictícia

- **Status:** Proposto — aguarda revisão do Thiago
- **Data:** 2026-10-09
- **Fase:** 2 — Interface
- **Decidido por:** Claude, por delegação do Thiago ("tome as melhores decisões"); **aguarda revisão do Thiago**

## Contexto

O repositório é **público** e o dono quer usá-lo como portfólio. Extratos reais trazem nomes, CPF parcial, números de conta e a vida financeira de terceiros (quem recebeu Pix).

## Decisão

Dado real nunca entra no repositório: `samples/`, `*.db` e `.env` ficam no `.gitignore`. Testes usam `tests/fixtures/` e a demonstração usa `data/demo/`, ambos **100% fictícios**, gerados de forma determinística por `scripts/gerar_demo.py`. Um teste confirma que a demonstração usa os marcadores fictícios (empresa "Exemplo", CNPJ de mentira); ele não prova a ausência de dado real, por isso o campo "Dados" do template de PR existe.

## Consequências

- Qualquer pessoa vê o app funcionando (`./run.sh demo`) sem expor nada do dono.
- Antes de cada commit, vale conferir o diff por nomes e números de conta (campo "Dados" no template de PR).
- Este ADR cobre o repositório. O que o dono envia a assistentes de IA durante o desenvolvimento é registrado em `docs/processo-de-trabalho.md`.
