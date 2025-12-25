#!/usr/bin/env bash
set -euo pipefail

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
  exit 1
fi

# Best-effort: create verifier log directory (may be a bind mount).
mkdir -p /logs/verifier 2>/dev/null || true

# Capture verifier output for debugging in Harbor/Jenkins artifacts.
# (Harbor often only surfaces a small stdout snippet; we keep full logs under /logs/verifier.)
exec 1> >(tee -a /logs/verifier/test-stdout.txt) 2> >(tee -a /logs/verifier/test-stderr.txt >&2)

# Best-effort: relax permissions in case the host created /logs with restrictive modes.
chmod -R a+rwx /logs 2>/dev/null || true

# Remove any pre-existing reward file so the final reward is derived only from test outcomes.
rm -f /logs/verifier/reward.txt 2>/dev/null || true

# Ensure HOME is set for uv installer.
: "${HOME:=/tmp}"
export HOME

# Install pinned test dependencies at test time (not in the runtime image).
# Prefer pip (simpler). Fall back to uvx if pip install fails.
set +e

python3 - <<'PY'
import sys
print("Python:", sys.version)
PY

python3 -m pip --version
python3 -m pip install --no-cache-dir -q "pytest==8.4.1" "pytest-json-ctrf==0.3.5"
PIP_INSTALL_EXIT=$?

if [ $PIP_INSTALL_EXIT -eq 0 ]; then
  python3 -m pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
  PYTEST_EXIT=$?
else
  echo "pip install failed (exit=$PIP_INSTALL_EXIT); falling back to uvx" >&2
  # Install uv/uvx at test time (pinned) if not present.
  if ! command -v uvx >/dev/null 2>&1; then
    python3 - <<'PY'
import urllib.request

url = "https://astral.sh/uv/0.9.5/install.sh"
dest = "/tmp/uv-install.sh"
urllib.request.urlretrieve(url, dest)
print(dest)
PY
    # Use bash explicitly; some environments have a very minimal /bin/sh.
    bash /tmp/uv-install.sh >/tmp/uv-install.log 2>&1 || true
  fi

  export PATH="$HOME/.local/bin:$PATH"
  if command -v uvx >/dev/null 2>&1; then
    uvx \
      -p 3.13 \
      -w pytest==8.4.1 \
      -w pytest-json-ctrf==0.3.5 \
      pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
    PYTEST_EXIT=$?
  else
    echo "uvx is not available; cannot run tests" >&2
    PYTEST_EXIT=1
  fi
fi

set -e

# Always produce a reward file based on test results
if [ $PYTEST_EXIT -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi

echo "PYTEST_EXIT=$PYTEST_EXIT"
echo "Wrote reward=$(cat /logs/verifier/reward.txt 2>/dev/null || echo '?')"

# Exit 0 so Harbor can consume the reward file
exit 0
