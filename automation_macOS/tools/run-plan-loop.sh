#!/bin/bash
# Local runner script for macOS
# Usage: ./run-plan-loop.sh -PlanPath plan.md [-Mode hybrid] [-MaxRounds 999] [-Model gpt-5.3-codex] [-NoCap] [-Resume]

set -e

# Default values
PLAN_PATH=""
MODE="hybrid"
MAX_ROUNDS=999
MODEL="gpt-5.3-codex"
NO_CAP=false
RESUME=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -PlanPath)
            PLAN_PATH="$2"
            shift 2
            ;;
        -Mode)
            MODE="$2"
            shift 2
            ;;
        -MaxRounds)
            MAX_ROUNDS="$2"
            shift 2
            ;;
        -Model)
            MODEL="$2"
            shift 2
            ;;
        -NoCap)
            NO_CAP=true
            shift
            ;;
        -Resume)
            RESUME=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 -PlanPath <path> [-Mode hybrid|auto|manual] [-MaxRounds N] [-Model model] [-NoCap] [-Resume]"
            exit 1
            ;;
    esac
done

if [ -z "$PLAN_PATH" ]; then
    echo "Error: -PlanPath is required"
    echo "Usage: $0 -PlanPath <path> [-Mode hybrid|auto|manual] [-MaxRounds N] [-Model model] [-NoCap] [-Resume]"
    exit 1
fi

# Get tool root
TOOL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="$TOOL_ROOT/scripts/plan_loop.py"

# Build arguments
ARGS=("--plan" "$PLAN_PATH" "--mode" "$MODE" "--max-rounds" "$MAX_ROUNDS" "--model" "$MODEL")
if [ "$NO_CAP" = true ]; then
    ARGS+=("--no-cap")
fi
if [ "$RESUME" = true ]; then
    ARGS+=("--resume")
fi

# Run the Python script
python3 "$SCRIPT_PATH" "${ARGS[@]}"