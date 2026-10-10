# ADR 0003 — Chave de duplicata

- **Status:** Aceito
- **Data:** 2026-10-06
- **Fase:** 1 — Fundação
- **Decidido por:** Claude, por delegação do Thiago ("tome as melhores decisões"); **aguarda revisão do Thiago**

## Contexto

A escolha inicial do Thiago foi um hash de **data + valor + descrição**. Ao ler o CSV real da conta apareceram dois fatos: (1) existe uma coluna `Identificador`, mas **ela não é única** — o Pix no crédito aparece em duas linhas com o mesmo identificador e valores opostos; (2) a fatura **não tem identificador**, e traz compras idênticas no mesmo dia (duas corridas de mesmo valor).

## Decisão

- **Conta:** `identificador + valor + descrição + contador`, onde o contador numera as ocorrências idênticas dentro do arquivo.
- **Fatura:** `data + valor + título + contador`.

A chave é um SHA-256 e é única por `household_id`.

## Consequências

- Reimportar, ou importar arquivos que se sobrepõem, não duplica nada (testado).
- Ajusta a escolha original do Thiago em um ponto: usa o identificador quando ele existe. Se o Thiago preferir a regra original, este ADR é revogado por outro.
- Limite conhecido: o contador assume que o banco exporta o dia inteiro. Um arquivo que corta um dia ao meio pode numerar diferente de outro que o cobre inteiro.
