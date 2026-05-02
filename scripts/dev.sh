#!/usr/bin/env bash
#
# Boot PagerZero locally — backend on :8000, frontend on :3000.
#
# Usage:  ./scripts/dev.sh
# Stop:   Ctrl-C  (cleans up both processes)
#

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
FRONTEND_DIR="$REPO_ROOT/frontend"

# Defaults — override by exporting before running
: "${BACKEND_PORT:=8000}"
: "${FRONTEND_PORT:=3000}"
: "${PAGERZERO_LLM_BACKEND:=mock}"
: "${PAGERZERO_MOCK_LATENCY_S:=0.4}"

export PAGERZERO_LLM_BACKEND PAGERZERO_MOCK_LATENCY_S

# Color helpers (TTY only)
if [[ -t 1 ]]; then
  bold=$(printf '\033[1m')
  dim=$(printf '\033[2m')
  amber=$(printf '\033[38;5;214m')
  green=$(printf '\033[38;5;42m')
  reset=$(printf '\033[0m')
else
  bold=""
  dim=""
  amber=""
  green=""
  reset=""
fi

log() { printf "%s[pz]%s %s\n" "${amber}" "${reset}" "$1"; }

cleanup() {
  log "shutting down…"
  if [[ -n "${backend_pid:-}" ]] && kill -0 "$backend_pid" 2>/dev/null; then
    kill "$backend_pid" 2>/dev/null || true
  fi
  if [[ -n "${frontend_pid:-}" ]] && kill -0 "$frontend_pid" 2>/dev/null; then
    kill "$frontend_pid" 2>/dev/null || true
  fi
  wait 2>/dev/null || true
  log "done"
}
trap cleanup EXIT INT TERM

# Pre-flight checks — fail fast with clear messages
if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv not found. Install: https://github.com/astral-sh/uv" >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "error: npm not found. Install Node 22+." >&2
  exit 1
fi

# Make sure scenario data exists (cheap to regenerate every boot)
log "regenerating demo scenarios…"
(cd "$BACKEND_DIR" && uv run python scripts/generate_scenarios.py) >/dev/null

log "starting backend on :${BACKEND_PORT} (LLM=${PAGERZERO_LLM_BACKEND}, mock_latency=${PAGERZERO_MOCK_LATENCY_S}s)"
(cd "$BACKEND_DIR" && uv run uvicorn pagerzero.api.main:app \
    --port "$BACKEND_PORT" --log-level warning) &
backend_pid=$!

# Wait for backend to actually accept connections before booting frontend
for _ in {1..40}; do
  if curl -sf "http://127.0.0.1:${BACKEND_PORT}/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done
if ! curl -sf "http://127.0.0.1:${BACKEND_PORT}/api/health" >/dev/null 2>&1; then
  echo "error: backend failed to become ready on :${BACKEND_PORT}" >&2
  exit 1
fi
log "${green}backend ready${reset}  http://127.0.0.1:${BACKEND_PORT}"

log "starting frontend on :${FRONTEND_PORT}"
(cd "$FRONTEND_DIR" && NEXT_PUBLIC_API_BASE="http://127.0.0.1:${BACKEND_PORT}" \
    npm run dev -- --port "$FRONTEND_PORT") &
frontend_pid=$!

cat <<EOF

${bold}PagerZero is up.${reset}
  ${dim}backend  ->${reset} http://127.0.0.1:${BACKEND_PORT}/docs
  ${dim}frontend ->${reset} http://127.0.0.1:${FRONTEND_PORT}

  ${dim}Ctrl-C to stop both.${reset}

EOF

# Block until either process exits, then the trap cleans up the other.
# Avoid `wait -n` so this works on bash 3.2 (macOS default).
while kill -0 "$backend_pid" 2>/dev/null && kill -0 "$frontend_pid" 2>/dev/null; do
  sleep 0.5
done
