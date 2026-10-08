#!/usr/bin/env bash
# Shell launcher for RTK filter
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/rtk_filter.py" "$@"
exit $?
