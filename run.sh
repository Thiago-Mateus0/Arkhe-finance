#!/usr/bin/env bash
# Sobe o app em http://localhost:8000. Uso: ./run.sh   (ou: ./run.sh import samples/*.csv)
# Demonstração com dados fictícios (banco descartável demo.db):  ./run.sh demo
# Seus nomes (contas próprias, separados por ';'):  export FINANCAS_OWN_NAMES="SEU NOME COMPLETO"
set -euo pipefail
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -e .
if [ "${1:-}" = "demo" ]; then
  export FINANCAS_DB="${FINANCAS_DB:-demo.db}" FINANCAS_OWN_NAMES="JOAO PEDRO ALMEIDA"
  rm -f "$FINANCAS_DB"
  python scripts/gerar_demo.py >/dev/null
  python -m financas import data/demo/*.csv
  python -m financas orcamento "Transporte" 250 >/dev/null
  python -m financas orcamento "Delivery" 135 >/dev/null
  python -m financas orcamento "Alimentação" 200 >/dev/null
  python -m financas orcamento "Saúde" 100 >/dev/null
fi
if [ "${1:-}" = "import" ]; then shift; exec python -m financas import "$@"; fi
if [ "${1:-}" = "pluggy" ]; then shift; exec python -m financas pluggy "$@"; fi
exec uvicorn financas.api:app --host 127.0.0.1 --port 8000
