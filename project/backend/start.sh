#!/bin/bash
python -m app.seed || echo "Seed already done"
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}"
