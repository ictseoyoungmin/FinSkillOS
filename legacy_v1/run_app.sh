#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Missing .venv. Create it first, then install requirements.txt." >&2
  echo "Expected: .venv/bin/python" >&2
  exit 1
fi

if [[ ! -x ".venv/bin/streamlit" ]]; then
  echo "Streamlit is not installed in .venv. Installing requirements.txt..." >&2
  .venv/bin/pip install -r requirements.txt
fi

exec .venv/bin/streamlit run app.py --server.headless true
