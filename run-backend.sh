#!/usr/bin/env bash

# Simple helper to start the FastAPI backend server
# Usage: from this folder run: ./run-backend.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d "venv" ]; then
  # Activate virtualenv if present
  . "venv/bin/activate"
fi

# Make sure any shell-exported DATABASE_URL does not override .env
unset DATABASE_URL

echo "Starting backend on http://0.0.0.0:8000 ..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --ws wsproto

