#!/bin/bash
cd -- "$(dirname -- "$0")" || exit 1
./setup.sh "$@"
result=$?
printf '\nPress Return to close. '
read -r _
exit "$result"
