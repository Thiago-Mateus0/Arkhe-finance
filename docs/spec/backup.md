# Spec — Backup e restauração

O banco é um único arquivo SQLite (`financas.db`, ou o que `FINANCAS_DB` apontar) com dado financeiro real. Sem cópia, um disco perdido ou um comando errado apaga tudo.

## Comandos

| Comando | O que faz |
|---|---|
| `./run.sh backup` | Cria `financas-AAAAMMDD-HHMMSS.db` em `backups/` (ao lado do banco), confere a cópia e apaga as mais antigas |
| `./run.sh backup --dir PASTA` | Grava em outra pasta (disco externo, pasta sincronizada). Também vale `FINANCAS_BACKUP_DIR` |
| `./run.sh backup --manter N` | Guarda as N mais novas (padrão 30; `0` guarda todas) |
| `./run.sh restaurar ARQUIVO` | Cria o banco a partir do backup, se ainda não existir um |
| `./run.sh restaurar ARQUIVO --sim` | Substitui o banco atual pelo backup, guardando antes uma cópia do atual |

(Sem o `run.sh`: `python -m financas backup` e `python -m financas restaurar`.)

## Garantias

- **Cópia consistente com o app aberto:** usa o backup do próprio SQLite; não copia o arquivo "no susto".
- **Conferida antes de valer:** a cópia só ganha o nome final depois de passar na checagem de integridade do SQLite e de ter a tabela de lançamentos. O resultado mostra a contagem de lançamentos, regras e orçamentos.
- **O banco de origem não é alterado.**
- **Só o dono lê:** o arquivo fica com permissão `600`.
- **Retenção segura:** só são apagadas cópias com o nome do backup automático (`financas-AAAAMMDD-HHMMSS.db`); qualquer outro arquivo na pasta, e as cópias de segurança de restauração, ficam.
- **Restaurar não destrói em silêncio:** recusa arquivo corrompido ou que não seja do app sem tocar no banco atual; para substituir um banco existente exige `--sim` e guarda antes `financas-…-antes-da-restauracao.db`.

## O que não faz

- **Não criptografa** o arquivo. Guarde em disco ou pasta que já seja só sua. Criptografia entra junto da hospedagem (ADR 0024), se for necessária.
- **Não copia para fora da máquina sozinho:** uma cópia ao lado do banco protege de engano, não de perda do disco. Aponte `--dir` para um disco externo ou pasta sincronizada.
- **Não agenda:** rodar de tempos em tempos (ou antes de importar um mês grande) é com o dono; um agendamento pode vir depois.

## Dado real

Backups têm dado real. `backups/`, `*.db`, `*.db.bak` e `*.bak` estão no `.gitignore`. Nunca vão para o git nem para o chat.
