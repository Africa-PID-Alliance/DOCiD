#!/bin/bash

# DOCiD Frontend Production Deployment Script
# This script creates a production-ready zip file for server deployment

set -e  # Exit on any error

echo "🚀 Starting DOCiD Frontend Production Deployment Package..."

# Check if build exists
if [ ! -d ".next" ]; then
    echo "❌ Build directory (.next) not found. Running production build first..."
    npm run build
else
    echo "✅ Build directory found"
fi

# Define deployment filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEPLOYMENT_ZIP="docid-frontend-${TIMESTAMP}.zip"

echo "📦 Creating deployment package: ${DEPLOYMENT_ZIP}"

# Create deployment zip with essential production files
zip -r "${DEPLOYMENT_ZIP}" \
    .next \
    public \
    package.json \
    package-lock.json \
    .env.production \
    next.config.mjs \
    ecosystem.config.js \
    next-i18next.config.js \
    jsconfig.json \
    -x "*.DS_Store" "*/.DS_Store" "*.log" "*/__pycache__/*" "*/node_modules/*" 2>/dev/null || \
zip -r "${DEPLOYMENT_ZIP}" \
    .next \
    public \
    package.json \
    package-lock.json \
    .env.production \
    -x "*.DS_Store" "*/.DS_Store" "*.log" "*/__pycache__/*" "*/node_modules/*"

echo "✅ Deployment package created successfully: ${DEPLOYMENT_ZIP}"

# Display package info
PACKAGE_SIZE=$(du -h "${DEPLOYMENT_ZIP}" | cut -f1)
echo "📊 Package size: ${PACKAGE_SIZE}"

echo ""
echo "🎯 Deployment Instructions:"
echo "1. Upload ${DEPLOYMENT_ZIP} to your server"
echo "2. Extract: unzip ${DEPLOYMENT_ZIP}"
echo "3. Install dependencies: npm ci --production"
echo "4. Start application: npm start (or pm2 start ecosystem.config.js)"
echo ""
echo "🌐 Production API URL: https://docid.africapidalliance.org/api/v1"
echo "✨ Deployment package ready!"