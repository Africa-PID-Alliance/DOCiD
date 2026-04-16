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

# Pipe a heredoc to bash on the server — avoids all quoting issues
ssh_exec() {
  sshpass -p "${SSH_PASS}" ssh -o StrictHostKeyChecking=no -p "${SSH_PORT}" \
    "${SSH_USER}@${SSH_HOST}" bash -s
}

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
ok()   { echo "OK  $*"; }
fail() { echo "FAIL $*" >&2; exit 1; }

# ── Preflight ─────────────────────────────────────────────────────────────────
command -v sshpass >/dev/null 2>&1 || fail "sshpass not found — install: brew install hudochenkov/sshpass/sshpass"

log "Cloning repo on server"
ssh_exec << ENDSSH
set -e
rm -rf ${REPO_DIR}
git clone --depth 1 ${REPO_URL} ${REPO_DIR}
ENDSSH
ok "Repo cloned to ${REPO_DIR}"

# ── Backend ───────────────────────────────────────────────────────────────────
if [ "${DEPLOY_BACKEND}" = true ]; then
  log "Deploying Backend"

  ssh_exec << ENDSSH
set -e
rsync -rlt --delete --no-perms --no-group --no-owner --omit-dir-times \
  --exclude='venv' \
  --exclude='.env' \
  --exclude='logs' \
  --exclude='uploads' \
  --exclude='__pycache__' \
  ${REPO_DIR}/backend/ /home/tcc-africa/docid_project/backend-v2/
ENDSSH
  ok "Backend files synced"

  ssh_exec << ENDSSH
set -e
cd /home/tcc-africa/docid_project/backend-v2
source venv/bin/activate
pip install -r requirements.txt --quiet
ENDSSH
  ok "Dependencies installed"

  ssh_exec << ENDSSH
set -e
cd /home/tcc-africa/docid_project/backend-v2
source venv/bin/activate
export FLASK_APP=run.py
flask db upgrade
ENDSSH
  ok "Migrations applied"

  log "Restarting Backend"
  OLD_PID=$(ssh_exec << 'ENDSSH'
pgrep -fo 'gunicorn.*wsgi:app' || echo ""
ENDSSH
)

  SUDO_PASS="${SSH_PASS}"
  ssh_exec << ENDSSH
echo '${SUDO_PASS}' | sudo -S supervisorctl restart docid
ENDSSH
  sleep 4

  NEW_PID=$(ssh_exec << 'ENDSSH'
pgrep -fo 'gunicorn.*wsgi:app' || echo ""
ENDSSH
)

  if [ -z "${NEW_PID}" ]; then
    fail "gunicorn not running after restart"
  fi
  ok "Backend restarted (PID ${OLD_PID} -> ${NEW_PID})"
fi

# ── Frontend ──────────────────────────────────────────────────────────────────
if [ "${DEPLOY_FRONTEND}" = true ]; then
  log "Deploying Frontend"

  ssh_exec << ENDSSH
set -e
rsync -rlt --delete --no-perms --no-group --no-owner --omit-dir-times \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='.env.production' \
  --exclude='logs' \
  ${REPO_DIR}/frontend/ /var/www/html/fe/
ENDSSH
  ok "Frontend files synced"

  log "Building Frontend (this takes ~1 min)"
  ssh_exec << 'ENDSSH'
set -e
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
cd /var/www/html/fe
npm ci
npm run build
ENDSSH
  ok "Frontend built"

  ssh_exec << 'ENDSSH'
set -e
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
cd /var/www/html/fe
pm2 restart docid-frontend || pm2 start ecosystem.config.js --env production
pm2 save
ENDSSH
  ok "Frontend restarted"
fi

# ── Cleanup ───────────────────────────────────────────────────────────────────
log "Cleanup"
ssh_exec << ENDSSH
rm -rf ${REPO_DIR}
ENDSSH
ok "Temp files removed"

# ── Health Checks ─────────────────────────────────────────────────────────────
log "Health Checks"
sleep 5

if [ "${DEPLOY_BACKEND}" = true ]; then
  ssh_exec << 'ENDSSH' && ok "Backend: OK" || fail "Backend health check FAILED"
curl -sf http://localhost:5001/api/v1/publications/get-list-resource-types > /dev/null
ENDSSH
fi

if [ "${DEPLOY_FRONTEND}" = true ]; then
  ssh_exec << 'ENDSSH' && ok "Frontend: OK" || fail "Frontend health check FAILED"
curl -sf http://localhost:3000 > /dev/null
ENDSSH
fi

echo ""
echo "Deploy complete"
