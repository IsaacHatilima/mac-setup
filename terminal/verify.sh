#!/bin/bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_bin="$(command -v python3 || true)"
[[ -n "$python_bin" ]] || { echo 'Python 3 is needed for verification.' >&2; exit 1; }
for file in "$ROOT"/*.sh "$ROOT"/*.command; do /bin/bash -n "$file"; done
for file in "$ROOT"/shell/*.zsh; do /bin/zsh -n "$file"; done
PYTHONDONTWRITEBYTECODE=1 "$python_bin" -m unittest discover -s "$ROOT/tests" -v
