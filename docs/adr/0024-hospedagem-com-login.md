# ADR 0024 — Hospedagem com login para uso por duas pessoas

- **Status:** Substituído pelo [ADR 0025](0025-supabase-como-backend-hospedado.md) (o Thiago escolheu Supabase). Os requisitos de segurança abaixo continuam valendo
- **Data:** 2026-10-14
- **Fase:** 6 — Automático e compartilhado
- **Decidido por:** Thiago pediu "hospedar de verdade, com login (fase 6)"; respondeu P20 (**casas separadas**) e preferiu o Supabase às opções A, B e C abaixo. As opções ficam como registro do que foi comparado
- **Completa:** [ADR 0008](0008-household-id-desde-o-inicio.md) ("autenticação só entra quando houver compartilhamento")

## Contexto

Até aqui o app roda **local**, no computador do dono, escutando só em `127.0.0.1`, sem login e sem enviar dado financeiro a ninguém (README e ADR 0008). Hospedar de verdade **muda essa premissa**: dado financeiro real passa a viver num servidor e a ser acessado pela internet, por duas pessoas.

Isso traz riscos que hoje não existem:

- **Exposição:** a API não tem autenticação e devolve extratos inteiros. Qualquer rota alcançável é vazamento.
- **Segredos:** o Meu Pluggy (ADR 0020) usa credenciais que hoje ficam só na máquina do dono. No servidor elas passam a morar lá.
- **Dado de outra pessoa:** a segunda pessoa passa a ter o dinheiro dela num sistema do Thiago. Isso exige que ela concorde e que um não enxergue o do outro, quando forem casas separadas.
- **Perda:** o banco é um arquivo SQLite. Sem backup testado, um disco perdido apaga tudo.
- **Documentação aberta:** o FastAPI publica `/docs` e `/openapi.json` por padrão, o que descreve toda a API a quem alcançar o servidor.

## Perguntas que só o Thiago responde

1. **Mesma casa ou casas separadas?** O modelo já tem `household_id`. (a) *Mesma casa*: as duas pessoas veem os mesmos lançamentos, regras e orçamentos; o login só identifica quem é quem. (b) *Casas separadas*: cada pessoa vê só o que é seu. Muda o login, os testes e a tela.
2. **Aceita dado real num servidor de terceiro?** A alternativa que mantém o dado em casa é a opção A abaixo.
3. **Quem é a segunda pessoa e ela concorda?** Os dados dela entram aqui.

## Opções

### Onde roda

| | Opção | Prós | Contras |
|---|---|---|---|
| **A** | **Em casa, atrás de rede privada** (VPN do tipo Tailscale), sem porta pública | Dado continua na máquina do dono; nada exposto à internet; custo de servidor zero | O computador precisa estar ligado; a outra pessoa instala o cliente da VPN |
| **B** | **Servidor pequeno próprio** (VPS), um contêiner com FastAPI e SQLite em disco persistente, HTTPS por proxy reverso | Sempre no ar; controle total; barato | Você mantém sistema, atualização, firewall e backup |
| **C** | **Plataforma gerenciada** com volume persistente | Subir é simples; HTTPS pronto | SQLite exige **uma única instância** e disco persistente; confiança em terceiro; custo e limites a conferir |

### Como entra (login)

| | Opção | Prós | Contras |
|---|---|---|---|
| **L1** | **Identidade na borda**: a rede privada (A) ou um proxy de acesso (B/C) autentica e repassa quem é; o app só lê a identidade | O app **não guarda senha**; menos superfície; segundo fator vem do provedor | Depende do provedor; o app precisa **recusar** requisição sem identidade (falhar fechado) |
| **L2** | **Login próprio** (usuário e senha com hash forte, cookie de sessão `HttpOnly`, limite de tentativas) | Independente de terceiro | Senha financeira própria é superfície a manter e a errar; recuperar senha, bloqueio, tudo seu |
| **L3** | **Senha única compartilhada** (HTTP Basic sobre HTTPS) | Mínimo possível | Não distingue as duas pessoas; inútil para "casas separadas" |

## Recomendação

**Não foi esta a escolha final.** O Thiago optou por Supabase (ver ADR 0025). A recomendação original era a opção A com L1; a opção B com L1 era a alternativa que mantinha o código atual.

## Requisitos de segurança (valem em qualquer opção)

- **Falhar fechado:** com hospedagem ligada, sem identidade válida a resposta é 401, em **todas** as rotas da API (não só nas novas).
- **Isolamento com teste:** o usuário A nunca lê, grava ou apaga dado do B (regra 5 do CLAUDE.md: testar as leituras possíveis). Cobre lançamentos, regras, orçamentos, nomes próprios, importação e Pluggy.
- **HTTPS obrigatório**, cookies `Secure`/`HttpOnly`/`SameSite`, e proteção contra requisição forjada nas rotas que alteram dado.
- **Fechar o que não precisa:** desligar `/docs` e `/openapi.json`; limitar tamanho de upload do CSV; CORS fechado.
- **Log sem valor:** descrição, contraparte e valor de lançamento **nunca** vão para log.
- **Segredos por variável de ambiente**, nunca no git (regra 1 e ADR 0007). Credenciais do Pluggy só depois de o login existir.
- **Backup:** cópia consistente do SQLite (`.backup`), criptografada, fora do servidor, **com restauração testada**.
- **Dado real não passa por mim:** a migração do banco local para o servidor é feita pelo Thiago, no computador dele. Nenhum extrato, banco ou credencial entra no repositório ou no chat.

## Etapas (um PR cada, depois do aceite)

1. **Identidade e isolamento:** o app lê a identidade, mapeia para `household_id` e recusa o que não tiver. Atrás de uma variável de ambiente, **desligado por padrão** (o uso local não muda). Testes de isolamento.
2. **Imagem do contêiner:** build do front e do backend, banco em volume, sem `/docs`.
3. **Backup e restauração**, com roteiro de teste.
4. **Guia de publicação** (rede privada, e a VPS se escolhida) e roteiro da migração feita pelo Thiago.
5. **Meu Pluggy no servidor**, com credenciais por variável de ambiente.

## Consequências

- O projeto deixa de ser "só local". README, ADR 0008 (a frase "não deve ser exposta") e o CLAUDE.md passam a distinguir **uso local** (sem login, `127.0.0.1`) de **hospedado** (com login obrigatório). Nada disso é editado antes do aceite.
- `household_id` deixa de ser só preparação e passa a ser fronteira de segurança, o que eleva a exigência de teste em toda consulta.
- Node continua necessário só para construir; na imagem final ele não precisa estar presente.
- **Custo e limites** de cada opção devem ser conferidos na hora de escolher; este ADR não assume valores.
- Se a resposta à pergunta 2 for "não", a opção A é a única compatível e as opções B e C saem.
