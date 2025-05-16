#!/usr/bin/env bash

# Enable error reporting and command echo
set -e
set -x

echo "=== RUNPOD SERVERLESS CONTAINER INITIALIZATION ==="
echo "Current directory: $(pwd)"
echo "Directory listing:"
ls -la

echo "=== CHECKING ENVIRONMENT ==="
echo "Python version:"
python3 --version

echo "=== CHECKING VIRTUAL ENVIRONMENT ==="
if [ -d "/workspace/.venv" ]; then
    echo "Virtual environment exists"
else
    echo "ERROR: Virtual environment not found"
fi

echo "=== STARTING RUNPOD HANDLER ==="
export PYTHONUNBUFFERED=1
echo "Activating virtual environment"
source /workspace/.venv/bin/activate
echo "Changing to workspace directory"
cd /workspace
echo "Starting handler.py"
/usr/bin/uv run python -u handler.py