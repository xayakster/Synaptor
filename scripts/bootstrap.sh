#!/usr/bin/env bash
# Shell launcher for Universal Agent Infrastructure Bootstrap
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/bootstrap-agent-environment.py" "$@"
exit $?
