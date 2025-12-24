pipeline {
  agent { 
    label 'Linux-01'
  }

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    // This repo IS the Harbor task (root contains instruction.md, task.toml, etc)
    TASK_PATH = '.'
    OPENAI_BASE_URL = 'https://api.portkey.ai/v1'
    // Set to 'true' in Jenkins job env to push logs back to Git.
    PUSH_LOGS_TO_GIT = 'false'
    // Override Docker Compose project name to avoid @ characters from workspace suffixes
    COMPOSE_PROJECT_NAME = 'fixclisum'
  }

  stages {
    // `Prepare Workspace Permissions` stage removed — no ACL changes performed by Jenkins

    stage('Preflight') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs

echo "Node: $(hostname)"
echo "Workspace: $WORKSPACE"
echo "User: $(id -un)"

echo "Task path: $TASK_PATH"
if ! TASK_ABS="$(cd "$WORKSPACE/$TASK_PATH" 2>/dev/null && pwd -P)"; then
  echo "ERROR: TASK_PATH cannot be resolved from WORKSPACE"
  echo "WORKSPACE: $WORKSPACE"
  echo "TASK_PATH: $TASK_PATH"
  echo "PWD: $(pwd)"
  echo "Workspace contents:"
  ls -la
  exit 1
fi

echo "Task absolute path: $TASK_ABS"
if [ ! -d "$TASK_ABS" ]; then
  echo "ERROR: TASK_ABS does not exist: $TASK_ABS"
  exit 1
fi

echo "Checking Docker access..."
if ! docker version >/dev/null 2>&1; then
  echo ""
  echo "ERROR: Jenkins user cannot access Docker."
  echo "To fix: Add the agent service user to the docker group and restart the agent."
  echo "Example: sudo usermod -aG docker $(id -un) && sudo systemctl restart jenkins-agent"
  exit 1
fi

# Install Harbor CLI and ensure PATH
(
  set -euo pipefail
  curl -LsSf https://astral.sh/uv/install.sh | sh
  source "$HOME/.local/bin/env"
  uv tool install harbor==0.1.25 --python 3.13
  export PATH="$HOME/.local/bin:$PATH"
  harbor --help >/dev/null
) 2>&1 | tee logs/preflight.log
'''
      }
    }

    stage('Oracle') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs

export PATH="$HOME/.local/bin:$PATH"
if [ -f "$HOME/.local/bin/env" ]; then
  source "$HOME/.local/bin/env"
fi

command -v harbor >/dev/null || { echo "harbor not found in PATH (did Preflight run?)"; exit 127; }

TASK_ABS="$(cd "$WORKSPACE/$TASK_PATH" 2>/dev/null && pwd -P)"
echo "Task absolute path: $TASK_ABS"
harbor run --agent oracle --path "$TASK_ABS" --force-build 2>&1 | tee logs/oracle.log

RESULT_JSON="$(awk '/Results written to /{print $NF}' logs/oracle.log | tail -n1)"
if [ -z "$RESULT_JSON" ]; then
  echo "ERROR: Could not find result.json path in logs/oracle.log"
  exit 1
fi

if [ ! -f "$RESULT_JSON" ] && [ -f "$WORKSPACE/$RESULT_JSON" ]; then
  RESULT_JSON="$WORKSPACE/$RESULT_JSON"
fi

if [ ! -f "$RESULT_JSON" ]; then
  echo "ERROR: Harbor result file not found: $RESULT_JSON"
  exit 1
fi

echo ""
echo "========== Harbor Oracle result.json =========="
cat "$RESULT_JSON" || true
echo "========== Harbor Oracle job dir listing =========="
ls -la "$(dirname "$RESULT_JSON")" || true
echo "========== Harbor Oracle job.log =========="
cat "$(dirname "$RESULT_JSON")/job.log" || true
echo "========== Harbor Oracle trial directory =========="
TRIAL_DIR="$(find "$(dirname "$RESULT_JSON")" -mindepth 1 -maxdepth 1 -type d | head -n1)"
if [ -n "$TRIAL_DIR" ]; then
  echo "Trial dir: $TRIAL_DIR"
  ls -laR "$TRIAL_DIR" || true
  echo "--- Trial config.json ---"
  cat "$TRIAL_DIR/config.json" 2>/dev/null || echo "(no config.json)"
  echo "--- Agent oracle.txt ---"
  cat "$TRIAL_DIR/agent/oracle.txt" 2>/dev/null || echo "(no agent/oracle.txt)"
  echo "--- Trial stdout ---"
  cat "$TRIAL_DIR/stdout" 2>/dev/null || echo "(no stdout)"
  echo "--- Trial stderr ---"
  cat "$TRIAL_DIR/stderr" 2>/dev/null || echo "(no stderr)"
  echo "--- Test stdout (verifier/test-stdout.txt) ---"
  cat "$TRIAL_DIR/verifier/test-stdout.txt" 2>/dev/null || echo "(no test-stdout.txt)"
fi
echo "================================================="

PYTHON_BIN="$(command -v python3 || command -v python || true)"
if [ -z "$PYTHON_BIN" ]; then
  echo "ERROR: python/python3 not found; cannot validate Harbor result.json"
  exit 1
fi

"$PYTHON_BIN" - "$RESULT_JSON" <<'PY'
import json
import sys

if len(sys.argv) < 2:
    print("ERROR: result.json path argument missing")
    sys.exit(1)

path = sys.argv[1]

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

def max_errors(node):
    if isinstance(node, dict):
        m = 0
        for k, v in node.items():
            if isinstance(k, str) and k.lower() in ("n_errors", "errors"):
                try:
                    m = max(m, int(v))
                except Exception:
                    pass
            m = max(m, max_errors(v))
        return m
    if isinstance(node, list):
        return max((max_errors(x) for x in node), default=0)
    return 0

err = max_errors(data)
print(f"Harbor reported errors: {err}")
sys.exit(1 if err > 0 else 0)
PY
'''
      }
    }

    stage('Checks') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs

export PATH="$HOME/.local/bin:$PATH"
if [ -f "$HOME/.local/bin/env" ]; then
  source "$HOME/.local/bin/env"
fi

command -v harbor >/dev/null || { echo "harbor not found in PATH (did Preflight run?)"; exit 127; }

TASK_ABS="$(cd "$WORKSPACE/$TASK_PATH" 2>/dev/null && pwd -P)"
echo "Task absolute path: $TASK_ABS"
harbor tasks check "$TASK_ABS" --model openai/@openai-tbench/gpt-5 2>&1 | tee logs/checks.log
'''
      }
    }

    stage('Agent Runs (optional)') {
      when {
        expression { return env.OPENAI_API_KEY?.trim() }
      }
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs

export PATH="$HOME/.local/bin:$PATH"
if [ -f "$HOME/.local/bin/env" ]; then
  source "$HOME/.local/bin/env"
fi

command -v harbor >/dev/null || { echo "harbor not found in PATH (did Preflight run?)"; exit 127; }

TASK_ABS="$(cd "$WORKSPACE/$TASK_PATH" 2>/dev/null && pwd -P)"
echo "Task absolute path: $TASK_ABS"

echo "Running GPT-5 agent..."
harbor run -a terminus-2 -m openai/@openai-tbench/gpt-5 -p "$TASK_ABS" 2>&1 | tee logs/agent-gpt5.log

RESULT_JSON="$(awk '/Results written to /{print $NF}' logs/agent-gpt5.log | tail -n1)"
if [ -z "$RESULT_JSON" ]; then
  echo "ERROR: Could not find result.json path in logs/agent-gpt5.log"
  exit 1
fi
if [ ! -f "$RESULT_JSON" ] && [ -f "$WORKSPACE/$RESULT_JSON" ]; then
  RESULT_JSON="$WORKSPACE/$RESULT_JSON"
fi
if [ ! -f "$RESULT_JSON" ]; then
  echo "ERROR: Harbor result file not found: $RESULT_JSON"
  exit 1
fi

echo ""
echo "========== Harbor Agent (GPT-5) result.json =========="
cat "$RESULT_JSON" || true
echo "========== Harbor Agent (GPT-5) job dir listing =========="
ls -la "$(dirname "$RESULT_JSON")" || true
echo "========== Harbor Agent (GPT-5) job.log =========="
cat "$(dirname "$RESULT_JSON")/job.log" || true
echo "========== Harbor Agent (GPT-5) trial directory =========="
TRIAL_DIR="$(find "$(dirname "$RESULT_JSON")" -mindepth 1 -maxdepth 1 -type d | head -n1)"
if [ -n "$TRIAL_DIR" ]; then
  echo "Trial dir: $TRIAL_DIR"
  ls -laR "$TRIAL_DIR" || true
  echo "--- Trial stdout ---"
  cat "$TRIAL_DIR/stdout" 2>/dev/null || echo "(no stdout)"
  echo "--- Trial stderr ---"
  cat "$TRIAL_DIR/stderr" 2>/dev/null || echo "(no stderr)"
fi
echo "========================================================"

PYTHON_BIN="$(command -v python3 || command -v python || true)"
if [ -z "$PYTHON_BIN" ]; then
  echo "ERROR: python/python3 not found; cannot validate Harbor result.json"
  exit 1
fi

"$PYTHON_BIN" - "$RESULT_JSON" <<'PY'
import json
import sys

if len(sys.argv) < 2:
    print("ERROR: result.json path argument missing")
    sys.exit(1)

path = sys.argv[1]

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

def max_errors(node):
    if isinstance(node, dict):
        m = 0
        for k, v in node.items():
            if isinstance(k, str) and k.lower() in ("n_errors", "errors"):
                try:
                    m = max(m, int(v))
                except Exception:
                    pass
            m = max(m, max_errors(v))
        return m
    if isinstance(node, list):
        return max((max_errors(x) for x in node), default=0)
    return 0

err = max_errors(data)
print(f"Harbor reported errors: {err}")
sys.exit(1 if err > 0 else 0)
PY

echo "Running Claude Sonnet 4.5 agent..."
harbor run -a terminus-2 -m openai/@anthropic-tbench/claude-sonnet-4-5-20250929 -p "$TASK_ABS" 2>&1 | tee logs/agent-claude.log

RESULT_JSON="$(awk '/Results written to /{print $NF}' logs/agent-claude.log | tail -n1)"
if [ -z "$RESULT_JSON" ]; then
  echo "ERROR: Could not find result.json path in logs/agent-claude.log"
  exit 1
fi
if [ ! -f "$RESULT_JSON" ] && [ -f "$WORKSPACE/$RESULT_JSON" ]; then
  RESULT_JSON="$WORKSPACE/$RESULT_JSON"
fi
if [ ! -f "$RESULT_JSON" ]; then
  echo "ERROR: Harbor result file not found: $RESULT_JSON"
  exit 1
fi

echo ""
echo "========== Harbor Agent (Claude) result.json =========="
cat "$RESULT_JSON" || true
echo "========== Harbor Agent (Claude) job dir listing =========="
ls -la "$(dirname "$RESULT_JSON")" || true
echo "========== Harbor Agent (Claude) job.log =========="
cat "$(dirname "$RESULT_JSON")/job.log" || true
echo "========== Harbor Agent (Claude) trial directory =========="
TRIAL_DIR="$(find "$(dirname "$RESULT_JSON")" -mindepth 1 -maxdepth 1 -type d | head -n1)"
if [ -n "$TRIAL_DIR" ]; then
  echo "Trial dir: $TRIAL_DIR"
  ls -laR "$TRIAL_DIR" || true
  echo "--- Trial stdout ---"
  cat "$TRIAL_DIR/stdout" 2>/dev/null || echo "(no stdout)"
  echo "--- Trial stderr ---"
  cat "$TRIAL_DIR/stderr" 2>/dev/null || echo "(no stderr)"
fi
echo "======================================================="

PYTHON_BIN="$(command -v python3 || command -v python || true)"
if [ -z "$PYTHON_BIN" ]; then
  echo "ERROR: python/python3 not found; cannot validate Harbor result.json"
  exit 1
fi

"$PYTHON_BIN" - "$RESULT_JSON" <<'PY'
import json
import sys

if len(sys.argv) < 2:
    print("ERROR: result.json path argument missing")
    sys.exit(1)

path = sys.argv[1]

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

def max_errors(node):
    if isinstance(node, dict):
        m = 0
        for k, v in node.items():
            if isinstance(k, str) and k.lower() in ("n_errors", "errors"):
                try:
                    m = max(m, int(v))
                except Exception:
                    pass
            m = max(m, max_errors(v))
        return m
    if isinstance(node, list):
        return max((max_errors(x) for x in node), default=0)
    return 0

err = max_errors(data)
print(f"Harbor reported errors: {err}")
sys.exit(1 if err > 0 else 0)
PY
'''
      }
    }

    stage('Publish Logs to Git (optional)') {
      when {
        expression { return env.PUSH_LOGS_TO_GIT?.trim()?.toLowerCase() == 'true' }
      }
      steps {
        withCredentials([usernamePassword(credentialsId: 'github-user', usernameVariable: 'GITHUB_USERNAME', passwordVariable: 'GITHUB_TOKEN')]) {
          sh '''#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs

git status --porcelain

git config user.email "jenkins@local"
git config user.name "jenkins"

# Push logs to a dedicated branch to avoid triggering your main pipeline.
LOG_BRANCH="jenkins-logs"

git fetch origin "+refs/heads/${LOG_BRANCH}:refs/remotes/origin/${LOG_BRANCH}" || true
git checkout -B "${LOG_BRANCH}" || true

git add -A logs

if git diff --cached --quiet; then
  echo "No log changes to publish."
  exit 0
fi

git commit -m "chore(logs): ${JOB_NAME} #${BUILD_NUMBER} [skip ci]"

# Use token auth for push
REPO_URL="$(git config --get remote.origin.url)"

# Normalize to https host/path
if [[ "$REPO_URL" =~ ^git@github.com:(.+)$ ]]; then
  REPO_URL="github.com/${BASH_REMATCH[1]}"
elif [[ "$REPO_URL" =~ ^https?://(.+)$ ]]; then
  REPO_URL="${BASH_REMATCH[1]}"
fi

git push "https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@${REPO_URL}" "${LOG_BRANCH}:${LOG_BRANCH}"
'''
        }
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'logs/**,jobs/**', allowEmptyArchive: true
    }
  }
}
