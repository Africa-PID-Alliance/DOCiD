#!/bin/bash
# deploy-check.sh — Run after deploy to verify all services are reachable
# Usage: ./deploy-check.sh (runs on the production server via SSH)

set -e

echo "=== DOCiD Deploy Health Check ==="
echo ""

ERRORS=0

# 1. Check Flask backend
FLASK_PORT=$(grep -oP "bind\s*=.*:(\d+)" /home/tcc-africa/docid_project/backend-v2/gunicorn.conf.py 2>/dev/null | grep -oP '\d+$' || echo "5001")
echo -n "[Flask] Checking port ${FLASK_PORT}... "
if curl -sf "http://127.0.0.1:${FLASK_PORT}/apidocs/" > /dev/null 2>&1; then
  echo "OK"
else
  echo "FAIL — Flask not responding on port ${FLASK_PORT}"
  ERRORS=$((ERRORS + 1))
fi

# 2. Check Next.js frontend
echo -n "[Next.js] Checking port 3000... "
if curl -sf "http://127.0.0.1:3000/" > /dev/null 2>&1; then
  echo "OK"
else
  echo "FAIL — Next.js not responding on port 3000"
  ERRORS=$((ERRORS + 1))
fi

# 3. Check BACKEND_API_URL in .env.production matches Flask port
if [ -f /var/www/html/fe/.env.production ]; then
  CONFIGURED_URL=$(grep "^BACKEND_API_URL=" /var/www/html/fe/.env.production | cut -d= -f2)
  echo -n "[Config] BACKEND_API_URL=${CONFIGURED_URL} ... "
  if curl -sf "${CONFIGURED_URL}/publications/1/views/count" > /dev/null 2>&1; then
    echo "OK"
  else
    echo "FAIL — Cannot reach Flask at configured BACKEND_API_URL"
    echo "  Expected Flask on port ${FLASK_PORT}, but BACKEND_API_URL=${CONFIGURED_URL}"
    ERRORS=$((ERRORS + 1))
  fi
else
  echo "[Config] WARNING: /var/www/html/fe/.env.production not found"
  ERRORS=$((ERRORS + 1))
fi

# 4. Check supervisor (Flask backend)
echo -n "[Supervisor] docid service... "
if sudo supervisorctl status docid 2>/dev/null | grep -q RUNNING; then
  echo "OK"
else
  echo "FAIL — docid supervisor service not running"
  ERRORS=$((ERRORS + 1))
fi

# 5. Check PM2 (Next.js frontend)
echo -n "[PM2] docid-frontend... "
if pm2 list 2>/dev/null | grep -q "online"; then
  echo "OK"
else
  echo "FAIL — PM2 processes not online"
  ERRORS=$((ERRORS + 1))
fi

echo ""
if [ $ERRORS -eq 0 ]; then
  echo "All checks passed!"
else
  echo "FAILED: ${ERRORS} check(s) failed. Review above."
  exit 1
fi
