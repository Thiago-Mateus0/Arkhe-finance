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

## Criptografado, para guardar na nuvem

`./run.sh backup --criptografar [--dir PASTA]` faz o mesmo backup conferido e o guarda como `financas-AAAAMMDD-HHMMSS.db.gpg`, protegido por uma senha que **você** escolhe (pelo menos 10 caracteres, digitada duas vezes).

- **Só o arquivo protegido chega ao destino.** A cópia sem senha existe apenas numa pasta temporária privada, apagada ao fim.
- **Conferido depois de protegido:** o arquivo é aberto com a senha e comparado ao original antes de ser guardado.
- **Abre sem este app:** é GnuPG padrão (AES-256). Em qualquer computador: `gpg -d financas-….db.gpg > financas.db`.
- **Guardar na nuvem:** aponte `--dir` para a pasta sincronizada, ou copie o `.db.gpg` para o site do serviço pelo navegador (arrastar e soltar).
- **Restaurar:** `./run.sh restaurar ARQUIVO.db.gpg [--sim]` pede a senha. Senha errada, arquivo alterado ou arquivo que **não foi criptografado com senha** (por exemplo uma mensagem OpenPGP sem criptografia, posta no lugar por quem alcança a pasta da nuvem) são recusados sem tocar no banco.
- **Agendar:** aponte `FINANCAS_BACKUP_SENHA_ARQUIVO` para um arquivo seu com a senha (permissão `600`; o app recusa se outras pessoas puderem ler).
- **Senha perdida = backup perdido.** Guarde num gerenciador de senhas. Nem este app nem ninguém recupera.
- **O que o serviço da nuvem ainda vê:** que existe um arquivo, o nome e o tamanho. Não o conteúdo.
- **Precisa do `gpg`** (`sudo apt install gnupg`). Sem ele o comando explica e não faz nada.

## Automático

Antes de **importar** (tela, `./run.sh import` e a API) e antes de **sincronizar com o Pluggy**, o app cria sozinho uma cópia `financas-AAAAMMDD-HHMMSS-antes-de-importar.db` (ou `-antes-de-sincronizar`) em `backups/`.

- Guarda as 10 mais novas de cada tipo; as cópias manuais e as de restauração não são tocadas.
- Vários arquivos importados em sequência (menos de 2 minutos) geram uma cópia só.
- **Nunca atrapalha a operação:** se não conseguir copiar (disco cheio, por exemplo), registra um aviso sem dado financeiro e a importação segue.
- Desligue com `FINANCAS_BACKUP_AUTO=0`.
- Uma cópia ao lado do banco protege de engano (importar errado, apagar regra), não de perda do disco: continue copiando para fora.

## Agendar (opcional)

O app não agenda sozinho. Para uma cópia por dia, em `crontab -e`:

```
0 21 * * * cd /caminho/do/app && ./run.sh backup --dir /caminho/do/disco-externo >> /tmp/financas-backup.log 2>&1
```

## Garantias

- **Cópia consistente com o app aberto:** usa o backup do próprio SQLite; não copia o arquivo "no susto".
- **Conferida antes de valer:** a cópia só ganha o nome final depois de passar na checagem de integridade do SQLite e de ter a tabela de lançamentos. O resultado mostra a contagem de lançamentos, regras e orçamentos.
- **O banco de origem não é alterado.**
- **Só o dono lê:** o arquivo fica com permissão `600`.
- **Retenção segura:** só são apagadas cópias com o nome do backup automático (`financas-AAAAMMDD-HHMMSS.db`); qualquer outro arquivo na pasta, e as cópias de segurança de restauração, ficam.
- **Restaurar não destrói em silêncio:** recusa arquivo corrompido ou que não seja do app sem tocar no banco atual; para substituir um banco existente exige `--sim` e guarda antes `financas-…-antes-da-restauracao.db`.

## O que não faz

- **Sem `--criptografar`, o arquivo não é protegido por senha.** Guarde em disco ou pasta que já seja só sua. O backup automático (antes de importar) também não é criptografado: fica ao lado do banco.
- **Não copia para fora da máquina sozinho:** uma cópia ao lado do banco protege de engano, não de perda do disco. Aponte `--dir` para um disco externo ou pasta sincronizada.
- **Não agenda sozinho:** veja "Agendar" acima.

## Dado real

Backups têm dado real. `backups/`, `*.db`, `*.db.bak` e `*.bak` estão no `.gitignore`. Nunca vão para o git nem para o chat.
