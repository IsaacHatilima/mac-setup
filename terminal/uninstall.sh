#!/bin/bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
for python_bin in /opt/homebrew/bin/python3 /usr/local/bin/python3; do
  if [[ -x "$python_bin" ]]; then exec "$python_bin" "$ROOT/scripts/configure.py" uninstall "$@"; fi
done
echo 'Python is required to restore the configuration safely.' >&2
exit 1
