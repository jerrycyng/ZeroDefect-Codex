#!/bin/bash
# Local runner for macOS
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$SCRIPT_DIR/tools/run-plan-loop.sh" "$@"