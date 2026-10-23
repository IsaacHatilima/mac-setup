#!/bin/bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_bin="$(command -v python3 || true)"
[[ -n "$python_bin" ]] || { echo 'Python 3 is needed for verification.' >&2; exit 1; }
for file in "$ROOT"/*.sh; do /bin/bash -n "$file"; done
PYTHONDONTWRITEBYTECODE=1 "$python_bin" -m unittest discover -s "$ROOT/tests" -v
