#!/usr/bin/env sh
set -eu
export PYTHONPATH="$(pwd)"
. .venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 18080
