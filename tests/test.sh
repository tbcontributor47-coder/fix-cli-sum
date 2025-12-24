#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier

# Ensure uv/uvx is available (pinned for reproducibility).
python -m pip install --no-cache-dir uv==0.9.5 >/logs/verifier/pip-uv-install.txt 2>&1

# Add uv to PATH (pip installs to ~/.local/bin)
export PATH="$HOME/.local/bin:$PATH"

# Run pytest and capture exit code
set +e
uvx \
  -p 3.13 \
  -w pytest==8.4.1 \
  -w pytest-json-ctrf==0.3.5 \
  pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
PYTEST_EXIT=$?
set -e

# Always produce a reward file based on test results
if [ $PYTEST_EXIT -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi

# Exit 0 so Harbor can consume the reward file
exit 0
