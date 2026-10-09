# Domain Docs

Como as skills de engenharia consomem a documentação de domínio deste repo.

## Antes de explorar, leia isto

- **`docs/spec/*.md`**: o que o sistema faz hoje, por área. Sem "porquê".
- **`docs/adr/*.md`**: decisões, uma por arquivo, nunca editadas depois de aceitas. Leia as que tocam a área em que vai mexer.
- **`docs/pendencias.md`**: o que falta decidir, por fase, e o status do projeto.

Repo single-context: não há `CONTEXT-MAP.md`.

## Vocabulário

Os termos de domínio vêm dos specs e dos ADRs (gasto, receita, repasse, transferência, fatura, categoria, pendente, condutor). Use-os como estão definidos. Se o conceito não existe em nenhum spec, é sinal: ou você está inventando linguagem, ou há lacuna real — registre em `docs/pendencias.md` em vez de decidir sozinho.

## Regra de número

Contagem, soma e porcentagem saem do banco ou da fixture na hora; não escreva o número no texto.

## Sinalize conflito com ADR

> _Contradiz ADR-000N (título), mas vale reabrir porque…_

ADR aceito não se edita: decisão nova revoga a antiga com um ADR novo apontando para o anterior.
