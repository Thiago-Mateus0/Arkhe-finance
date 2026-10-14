# ADR 0019 — Assinaturas são a categoria "Assinaturas", marcada pelo usuário

- **Status:** Aceito
- **Data:** 2026-10-14
- **Fase:** 4 — Controle
- **Decidido por:** Thiago

## Contexto

A pendência P5 propunha detectar cobranças que se repetem todo mês. Nos dados reais, as assinaturas que o dono conhece (academia, iFood Club, ambas no crédito) apareceram uma ou duas vezes, com valores diferentes, e o que mais se repetia (corridas, Pix para pessoas, aplicação) não é assinatura. Detecção automática perderia o que importa e traria ruído.

## Decisão

Assinatura é toda cobrança da categoria **Assinaturas**, definida por regra pelo usuário (tela de regras). O app só lê essa categoria: total do mês e lista das ativas, com valor e data da cobrança mais recente e a próxima estimada. Sem detecção automática.

## Consequências

- Reaproveita regras e categoria que já existem; não cria conceito novo no banco.
- Mover algo para Assinaturas o tira da categoria anterior (por exemplo, a academia deixa de ser Saúde).
- Não altera tipo nem totais de gasto; é leitura.
- Sugerir assinaturas automaticamente fica como ideia futura, e exigiria decisão nova.
