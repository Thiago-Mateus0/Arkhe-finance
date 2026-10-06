#!/usr/bin/env bash
# Sobe o app em http://localhost:8000. Uso: ./run.sh   (ou: ./run.sh import samples/*.csv)
# Seus nomes (contas próprias, separados por ';'):  export FINANCAS_OWN_NAMES="SEU NOME COMPLETO"
set -euo pipefail
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -e .
if [ "${1:-}" = "import" ]; then shift; exec python -m financas import "$@"; fi
exec uvicorn financas.api:app --host 127.0.0.1 --port 8000
