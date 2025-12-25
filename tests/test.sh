#!/usr/bin/env bash
set -euo pipefail

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
  exit 1
fi

# Best-effort: create verifier log directory (may be a bind mount).
mkdir -p /logs/verifier 2>/dev/null || true

# Best-effort: relax permissions in case the host created /logs with restrictive modes.
chmod -R a+rwx /logs 2>/dev/null || true

# Remove any pre-existing reward file so the final reward is derived only from test outcomes.
rm -f /logs/verifier/reward.txt 2>/dev/null || true

# Ensure HOME is set for uv installer.
: "${HOME:=/tmp}"
export HOME

# Prefer offline execution: if pytest + ctrf plugin are available in the image,
# run them directly. Fall back to uvx only if necessary.
set +e
python3 -c 'import pytest_json_ctrf' >/dev/null 2>&1
HAS_CTRF=$?
python3 -c 'import pytest' >/dev/null 2>&1
HAS_PYTEST=$?

if [ $HAS_PYTEST -eq 0 ] && [ $HAS_CTRF -eq 0 ]; then
  python3 -m pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
  PYTEST_EXIT=$?
else
  # Install uv/uvx at test time (pinned) if not present in the runtime image.
  if ! command -v uvx >/dev/null 2>&1; then
    python3 - <<'PY'
import urllib.request

url = "https://astral.sh/uv/0.9.5/install.sh"
dest = "/tmp/uv-install.sh"
urllib.request.urlretrieve(url, dest)
print(dest)
PY
    sh /tmp/uv-install.sh >/tmp/uv-install.log 2>&1 || true
  fi

  export PATH="$HOME/.local/bin:$PATH"
  uvx \
    -p 3.13 \
    -w pytest==8.4.1 \
    -w pytest-json-ctrf==0.3.5 \
    pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
  PYTEST_EXIT=$?
fi
set -e

# Always produce a reward file based on test results
if [ $PYTEST_EXIT -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi

# Exit 0 so Harbor can consume the reward file
exit 0
