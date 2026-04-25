#!/bin/bash

# DOCiD Frontend Production Deployment Script
# This script creates a production-ready zip file for server deployment
# Note: CI/CD via GitHub Actions is now the preferred deployment method

set -e  # Exit on any error

echo "🚀 Starting DOCiD Frontend Production Deployment Package..."

# Always rebuild to ensure latest changes are included
echo "🔨 Running production build..."
npm run build
echo "✅ Build completed"

# Define deployment filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEPLOYMENT_ZIP="docid-frontend-${TIMESTAMP}.zip"

echo "📦 Creating deployment package: ${DEPLOYMENT_ZIP}"

# Create deployment zip with essential production files
zip -r "${DEPLOYMENT_ZIP}" \
    .next \
    src \
    public \
    package.json \
    package-lock.json \
    .env.production \
    next.config.mjs \
    ecosystem.config.js \
    next-i18next.config.js \
    jsconfig.json \
    deploy-server.sh \
    -x "*.DS_Store" "*/.DS_Store" "*.log" "*/__pycache__/*" "*/node_modules/*" 2>/dev/null || \
zip -r "${DEPLOYMENT_ZIP}" \
    .next \
    src \
    public \
    package.json \
    package-lock.json \
    .env.production \
    deploy-server.sh \
    -x "*.DS_Store" "*/.DS_Store" "*.log" "*/__pycache__/*" "*/node_modules/*"

echo "✅ Deployment package created successfully: ${DEPLOYMENT_ZIP}"

# Display package info
PACKAGE_SIZE=$(du -h "${DEPLOYMENT_ZIP}" | cut -f1)
echo "📊 Package size: ${PACKAGE_SIZE}"

echo ""
echo "🎯 Deployment Instructions:"
echo "1. Upload ${DEPLOYMENT_ZIP} to your server"
echo "2. Extract: unzip ${DEPLOYMENT_ZIP}"
echo "3. Run: ./deploy-server.sh"
echo ""
echo "🌐 Production API URL: ${NEXT_PUBLIC_API_BASE_URL:-<set NEXT_PUBLIC_API_BASE_URL in env>}"
echo "✨ Deployment package ready!"