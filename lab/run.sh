#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-loom-190-adk-ci-glob}"
export LAB_URL="${LAB_URL:-http://127.0.0.1:18750}"
export PYTHONUNBUFFERED=1

PIN_TAG="v1.9.0"
PIN_SHA="a3050669f5b4c83210a44ed4346f17e01641e82f"
SRC_DEST="src-v1.9.0"
LABEL="LOOM-190-ADK-CI-GLOB"
WITNESS="LOOM-190-ADK-CI-GLOB-WITNESS"

compose_down() {
  echo "== docker compose down -v =="
  docker compose -p "${COMPOSE_PROJECT_NAME}" down -v --remove-orphans || true
}

finish() {
  local status=$?
  trap - EXIT
  compose_down
  exit "${status}"
}
trap finish EXIT


copy_pin() {
  local tmp got
  tmp="$(mktemp -d)"
  GIT_TERMINAL_PROMPT=0 git clone --depth 1 --branch "${PIN_TAG}" --filter=blob:none --sparse \
    https://github.com/awslabs/loom.git "${tmp}"
  git -C "${tmp}" sparse-checkout set agents/adk_agent agents/strands_agent
  got="$(git -C "${tmp}" rev-parse HEAD)"
  echo "checkout tag=${PIN_TAG} sha=${got} expect=${PIN_SHA}"
  if [[ "${got}" != "${PIN_SHA}" ]]; then
    GIT_TERMINAL_PROMPT=0 git -C "${tmp}" fetch --depth 1 origin "${PIN_SHA}"
    git -C "${tmp}" checkout -f "${PIN_SHA}"
    got="$(git -C "${tmp}" rev-parse HEAD)"
    echo "checkout-forced sha=${got}"
  fi
  if [[ "${got}" != "${PIN_SHA}" ]]; then
    rm -rf "${tmp}"
    echo "FAIL ${LABEL} unexpected-commit got=${got} expect=${PIN_SHA}" | tee poc-last-run.txt
    exit 1
  fi
  rm -rf "src-v1.9.0"
  mkdir -p "src-v1.9.0/agents"
  cp -a "${tmp}/agents/adk_agent" "src-v1.9.0/agents/"
  cp -a "${tmp}/agents/strands_agent" "src-v1.9.0/agents/"
  rm -rf "${tmp}"
  find "src-v1.9.0" -type d -name '__pycache__' -exec rm -rf {} + || true
  echo "checkout-ok tag=${PIN_TAG} sha=${got} source=public-tag"
}

echo "== pin ${PIN_TAG} ${PIN_SHA} =="
copy_pin

APPROVAL="${SRC_DEST}/agents/adk_agent/src/integrations/approval.py"
CI_PY="${SRC_DEST}/agents/adk_agent/src/integrations/code_interpreter.py"
STRANDS_AGENT="${SRC_DEST}/agents/strands_agent/src/agent.py"
if [[ ! -f "${APPROVAL}" || ! -f "${CI_PY}" || ! -f "${STRANDS_AGENT}" ]]; then
  echo "FAIL ${LABEL} missing-agent-tree ${WITNESS}" | tee poc-last-run.txt
  exit 1
fi
if ! grep -q 'fnmatch.fnmatch' "${APPROVAL}"; then
  echo "FAIL ${LABEL} approval-fnmatch-missing ${WITNESS}" | tee poc-last-run.txt
  exit 1
fi
if ! grep -q 'class ApprovalPolicyMatcher' "${APPROVAL}"; then
  echo "FAIL ${LABEL} matcher-class-missing ${WITNESS}" | tee poc-last-run.txt
  exit 1
fi
if ! grep -q 'FunctionTool(code_interpreter_execute_code)' "${CI_PY}"; then
  echo "FAIL ${LABEL} execute-code-tool-missing ${WITNESS}" | tee poc-last-run.txt
  exit 1
fi
if ! grep -q 'FunctionTool(code_interpreter_execute_command)' "${CI_PY}"; then
  echo "FAIL ${LABEL} execute-command-tool-missing ${WITNESS}" | tee poc-last-run.txt
  exit 1
fi
if ! grep -q 'tools.append(ci.code_interpreter)' "${STRANDS_AGENT}"; then
  echo "FAIL ${LABEL} strands-register-missing ${WITNESS}" | tee poc-last-run.txt
  exit 1
fi

echo "== py_compile =="
python3 -m py_compile poc.py lab_server.py
rm -rf __pycache__

echo "== docker compose down (clean) =="
compose_down

echo "== docker compose up --build =="
up_ok=0
for attempt in $(seq 1 8); do
  if docker compose -p "${COMPOSE_PROJECT_NAME}" up --build -d; then
    up_ok=1
    break
  fi
  echo "compose-up-retry attempt=${attempt}"
  sleep 5
  compose_down
done
if [[ "${up_ok}" != 1 ]]; then
  echo "FAIL ${LABEL} compose up failed ${WITNESS}" | tee poc-last-run.txt
  exit 1
fi

echo "== wait /health =="
ready=0
code=""
for i in $(seq 1 40); do
  code="$(curl -sS -o /tmp/loom-190-adk-ci-glob-health.json -w '%{http_code}' --max-time 5 "${LAB_URL}/health" || true)"
  if [[ "${code}" == "200" ]]; then
    ready=1
    echo "health-ready attempt=${i} http=${code}"
    break
  fi
  echo "health-wait attempt=${i} http=${code}"
  sleep 1
done
if [[ "${ready}" != 1 ]]; then
  echo "FAIL ${LABEL} matcher not ready http=${code} ${WITNESS}" | tee poc-last-run.txt
  docker compose -p "${COMPOSE_PROJECT_NAME}" logs --tail=120 || true
  exit 1
fi

echo "== poc.py =="
set +e
python3 ./poc.py | tee poc-last-run.txt
rc=${PIPESTATUS[0]}
set -e
if ! grep -qE "FAIL ${LABEL}|SUCCESS ${LABEL}" poc-last-run.txt; then
  echo "FAIL ${LABEL} poc-no-verdict exit=${rc} ${WITNESS}" >> poc-last-run.txt
  rc=1
fi
exit "${rc}"
