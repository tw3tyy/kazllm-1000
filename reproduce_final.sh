#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
exec bash run_project_python.sh final_reproduce.py "$@"
