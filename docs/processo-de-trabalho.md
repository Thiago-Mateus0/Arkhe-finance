# Como este projeto é construído

Projeto solo, de uso pessoal, que também serve de portfólio. Este documento descreve o processo como ele aconteceu, sem enfeite.

## Papéis

- **Thiago** decide o que o sistema faz: escopo, regras de classificação, o que fica para depois, o que conta como gasto. Faz o merge de todo PR.
- **Claude Code** (assistente de IA, em sessões na nuvem) escreve boa parte do código, dos testes e dos rascunhos de spec e ADR, e verifica o resultado no navegador. Vai aparecer commit com `Co-Authored-By: Claude` no histórico.

## Como uma funcionalidade nasce

1. **Entrevista.** O Claude faz perguntas até o desenho ficar fechado (skill `grilling`); o Thiago responde e decide.
2. **Spec e ADR.** O que ficou decidido vira texto: spec para o "o quê", ADR para o "porquê". Quando o Thiago delegou a decisão técnica ("tome as melhores decisões"), o ADR nasce **Proposto** e só vira **Aceito** depois da revisão dele.
3. **Código com teste.** Primeiro o teste do que é regra de dinheiro; depois a implementação. Bug real vira teste.
4. **Verificação.** A suíte (`python -m pytest -q`) e, para interface, abrir no navegador e olhar a captura de tela.
5. **PR pequeno** com "O que conferir": até 3 linhas que o Thiago valida sem ler código. O merge é dele.

## Dados reais e IA

Para validar o importador, extratos reais do Thiago foram usados em sessões com o assistente, **fora do repositório** (`samples/` é ignorado pelo git). O repositório é público e só contém dados fictícios (`tests/fixtures/`, `data/demo/`). Ver ADR 0007.

## Regras que o projeto adotou

1. **Número vem do dado, nunca do texto.**
2. **Spec fala o quê; ADR fala por quê.** "Porque" dentro do spec é sinal de que deveria ser ADR.
3. **ADR aceito não se edita.** Decisão nova revoga a antiga com ADR novo.
4. **Regra de dinheiro só entra com teste das leituras possíveis dela.**
5. **Status não é spec.** Fase e andamento vivem em `docs/pendencias.md`.

O método vem do projeto [Lifetrailer Studio](https://github.com/Thiago-Mateus0/lifetrailer-studio), onde o mesmo processo é aplicado em um sistema maior.
