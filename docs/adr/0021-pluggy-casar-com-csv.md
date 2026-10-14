# ADR 0021 — Casar os lançamentos do Pluggy com os do CSV

- **Status:** Proposto — aguarda decisão do Thiago
- **Data:** 2026-10-14
- **Fase:** 6a — Fonte automática
- **Decidido por:** Claude propôs, com base em contagens feitas por script nos dados do Thiago (nenhum valor entra no repositório)

## Contexto

O ADR 0020 aceitou o Meu Pluggy como fonte automática. O CSV continua suportado, então o mesmo lançamento pode chegar pelos dois caminhos e ser contado em dobro. A comparação nos dados reais mostrou:

- **Conta:** valor e dia concordam; a data do Pluggy às vezes difere em 1 dia. Casar por valor e data com tolerância de 1 dia, um para um, cobre quase todos.
- **Cartão:** a data do CSV de fatura não é a da compra; é a data em que a compra foi lançada na fatura (`billPostDate`). Por ela, quase tudo casa.
- **Direção:** na conta, o sinal do valor acompanha `type`; no cartão o sinal vem **invertido**. A direção deve vir sempre de `type` (`DEBIT` ou `CREDIT`), nunca do sinal.
- **Pendentes:** compras de cartão `PENDING` mudam depois de faturadas.

## Decisão proposta

1. **Chave de casamento:** mesma conta, valor absoluto igual e data até 1 dia de diferença, consumindo um a um. Vale nos dois sentidos (importar Pluggy depois do CSV e CSV depois do Pluggy). Se casar, não duplica.
2. **Direção** pelo `type` do Pluggy.
3. **Só `POSTED`.** Pendente não entra.
4. **Cartão: data = `billPostDate`**, igual ao CSV, para o histórico não mudar. A data da compra (`purchaseDate`) fica guardada para uso futuro. *Alternativa:* passar a usar a data da compra, o que muda os totais de meses já fechados e exige decisão do Thiago.
5. **Parcelas** vêm de `installmentNumber` e `totalInstallments`.
6. **Tipos:** `PAGAMENTO_FATURA` do cartão é `card_payment`, como no CSV.

## Consequências

- Exige guardar a origem e o identificador externo do lançamento (mudança de esquema do banco).
- Reimportar qualquer das duas fontes continua sem mudar nada (regra 9).
- Cada regra acima precisa de teste das leituras possíveis (regra 5) antes de entrar.
- Fica fora desta decisão: tratar `RESGATE_APLIC_FINANCEIRA` (resgate de aplicação) como entrada ou como movimento próprio.
