#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
export PYTHONPATH="$PWD"

uvicorn apps.agent_service.app.main:app --host 0.0.0.0 --port "${AGENT_SERVICE_PORT:-8001}" --reload
