#!/usr/bin/env bash
# deploy.sh — Manual SSH deploy for DOCiD production
# Use when GitHub Actions billing is unavailable.
#
# Usage:
#   ./deploy.sh                  # full deploy (backend + frontend)
#   ./deploy.sh --backend-only   # backend only
#   ./deploy.sh --frontend-only  # frontend only

set -e

# ── Connection ────────────────────────────────────────────────────────────────
SSH_HOST="197.136.17.175"
SSH_PORT="62222"
SSH_USER="tcc-africa"
SSH_PASS='AP@-D0c!D2050'
REPO_URL="https://github.com/Africa-PID-Alliance/DOCiD.git"
REPO_DIR="/tmp/docid-deploy"

SSH_CMD="sshpass -p '${SSH_PASS}' ssh -o StrictHostKeyChecking=no -p ${SSH_PORT} ${SSH_USER}@${SSH_HOST}"

# ── Flags ─────────────────────────────────────────────────────────────────────
DEPLOY_BACKEND=true
DEPLOY_FRONTEND=true

for arg in "$@"; do
  case $arg in
    --backend-only|-b)  DEPLOY_FRONTEND=false ;;
    --frontend-only|-f) DEPLOY_BACKEND=false  ;;
  esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
log()  { echo ""; echo "=== $* ==="; }
ok()   { echo "✓  $*"; }
fail() { echo "✗  $*" >&2; exit 1; }

run() {
  # Run a command on the production server
  eval "${SSH_CMD} \"$*\""
}

# ── Preflight ─────────────────────────────────────────────────────────────────
command -v sshpass >/dev/null 2>&1 || fail "sshpass not found — install with: brew install hudochenkov/sshpass/sshpass"

log "Cloning repo on server"
run "rm -rf ${REPO_DIR} && git clone --depth 1 ${REPO_URL} ${REPO_DIR}"
ok "Repo cloned to ${REPO_DIR}"

# ── Backend ───────────────────────────────────────────────────────────────────
if [ "${DEPLOY_BACKEND}" = true ]; then
  log "Deploying Backend"

  run "rsync -rlt --delete --no-perms --no-group --no-owner --omit-dir-times \
    --exclude='venv' \
    --exclude='.env' \
    --exclude='logs' \
    --exclude='uploads' \
    --exclude='__pycache__' \
    ${REPO_DIR}/backend/ /home/tcc-africa/docid_project/backend-v2/"
  ok "Backend files synced"

  run "cd /home/tcc-africa/docid_project/backend-v2 && \
    source venv/bin/activate && \
    pip install -r requirements.txt --quiet"
  ok "Dependencies installed"

  run "cd /home/tcc-africa/docid_project/backend-v2 && \
    source venv/bin/activate && \
    export FLASK_APP=run.py && \
    flask db upgrade"
  ok "Migrations applied"

  log "Restarting Backend"
  OLD_PID=$(run "pgrep -fo 'gunicorn.*wsgi:app' || echo ''")

  run "echo '${SSH_PASS}' | sudo -S supervisorctl restart docid"
  sleep 4

  NEW_PID=$(run "pgrep -fo 'gunicorn.*wsgi:app' || echo ''")

  if [ -z "${NEW_PID}" ]; then
    fail "gunicorn not running after restart"
  fi
  if [ "${OLD_PID}" = "${NEW_PID}" ] && [ -n "${OLD_PID}" ]; then
    fail "gunicorn PID unchanged (${OLD_PID}) — restart did not take effect"
  fi
  ok "Backend restarted (PID ${OLD_PID} → ${NEW_PID})"
fi

# ── Frontend ──────────────────────────────────────────────────────────────────
if [ "${DEPLOY_FRONTEND}" = true ]; then
  log "Deploying Frontend"

  run "rsync -rlt --delete --no-perms --no-group --no-owner --omit-dir-times \
    --exclude='node_modules' \
    --exclude='.next' \
    --exclude='.env.production' \
    --exclude='logs' \
    ${REPO_DIR}/frontend/ /var/www/html/fe/"
  ok "Frontend files synced"

  run "export NVM_DIR=\"\$HOME/.nvm\" && \
    [ -s \"\$NVM_DIR/nvm.sh\" ] && . \"\$NVM_DIR/nvm.sh\" && \
    cd /var/www/html/fe && \
    npm ci && npm run build"
  ok "Frontend built"

  run "export NVM_DIR=\"\$HOME/.nvm\" && \
    [ -s \"\$NVM_DIR/nvm.sh\" ] && . \"\$NVM_DIR/nvm.sh\" && \
    cd /var/www/html/fe && \
    pm2 restart docid-frontend || pm2 start ecosystem.config.js --env production && pm2 save"
  ok "Frontend restarted"
fi

# ── Cleanup ───────────────────────────────────────────────────────────────────
log "Cleanup"
run "rm -rf ${REPO_DIR}"
ok "Temp files removed"

# ── Health Checks ─────────────────────────────────────────────────────────────
log "Health Checks"
sleep 5

if [ "${DEPLOY_BACKEND}" = true ]; then
  run "curl -sf http://localhost:5001/api/v1/health > /dev/null" \
    && ok "Backend: OK" || fail "Backend health check FAILED"
fi

if [ "${DEPLOY_FRONTEND}" = true ]; then
  run "curl -sf http://localhost:3000 > /dev/null" \
    && ok "Frontend: OK" || fail "Frontend health check FAILED"
fi

echo ""
echo "✓ Deploy complete"
