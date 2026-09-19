#!/bin/bash
set -e
python -m app.seed 2>/dev/null || echo "Seed skipped"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}"
