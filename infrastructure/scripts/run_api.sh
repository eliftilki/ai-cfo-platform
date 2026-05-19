#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
export PYTHONPATH="$PWD"

uvicorn apps.api.app.main:app --host 0.0.0.0 --port "${API_SERVICE_PORT:-8000}" --reload
