#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
bash run_project_python.sh site/build_site.py
bash run_project_python.sh website/build.py
