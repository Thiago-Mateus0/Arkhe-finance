# ADR 0005 — Repasse: pareamento exato e por soma

- **Status:** Proposto — aguarda revisão do Thiago
- **Data:** 2026-10-08
- **Fase:** 1 — Fundação
- **Decidido por:** Claude, por delegação do Thiago ("tome as melhores decisões"); **aguarda revisão do Thiago**

## Contexto

O extrato real tem muito dinheiro que passa pela conta sem ser do dono: amigos mandam Pix e o dono repassa o mesmo valor a um serviço de pagamento. Pareando só entrada e saída de valor idêntico no mesmo dia, sobravam saídas que eram a **soma** de duas entradas, às vezes de dias diferentes, e entradas falsas de poucos reais.

## Decisão

Duas fases: (1) pareamento exato (mesmo valor, mesmo dia); (2) uma saída restante é pareada com um conjunto de até 4 entradas, até 3 dias antes, de soma exata — **mas só se a contraparte da saída já tiver tido um repasse exato** (um *condutor*). Entre as combinações possíveis vale a mais recente.

## Consequências

- A restrição ao condutor impede esconder gasto de verdade: uma saída para uma loja qualquer nunca é tratada como repasse.
- A escolha da combinação mais recente nasceu de um erro real: preferir "um valor só" consumia uma receita legítima, de valor igual, de dois dias antes. Há teste para isso.
- Limite: repasse de valor que não fecha exatamente (taxas, centavos) não é detectado e vira gasto até o Thiago categorizar.
