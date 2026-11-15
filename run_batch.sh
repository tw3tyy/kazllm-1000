#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
limit="${1:-25}"
if ! [[ "$limit" =~ ^[1-9][0-9]*$ ]]; then
  echo 'Usage: ./run_batch.sh [positive new-request limit per model]' >&2
  exit 1
fi
failed=0
if ! ./run_gemini.sh --free-tier-confirmed --max-new "$limit" --continue-on-invalid; then
  failed=1
fi
for model in qwen2.5-7b gemma3; do
  if ! ./run_local.sh --model "$model" --max-new "$limit" --continue-on-invalid; then
    failed=1
  fi
done
./refresh_site.sh
./demo.sh --status
exit "$failed"
