#!/bin/bash

# DOCiD Frontend Server Deployment Script
# Run this script on the server after extracting the deployment package

set -e  # Exit on error

echo "🚀 DOCiD Frontend Server Deployment"
echo "===================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="docid-frontend"
PORT=${PORT:-3000}
NODE_ENV="production"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check prerequisites
echo ""
echo "Checking prerequisites..."

if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js first."
    exit 1
fi

if ! command_exists npm; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

if ! command_exists pm2; then
    print_info "PM2 is not installed. Installing PM2 globally..."
    npm install -g pm2
    print_success "PM2 installed successfully"
fi

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    print_error ".env.production file not found!"
    echo "Please ensure .env.production exists with:"
    echo "NEXT_PUBLIC_API_BASE_URL=https://docid.africapidalliance.org/api/v1"
    exit 1
fi

# Install dependencies
echo ""
echo "Installing production dependencies..."
npm ci --production
print_success "Dependencies installed"

# Stop existing PM2 process if running
if pm2 list | grep -q "$APP_NAME"; then
    print_info "Stopping existing $APP_NAME process..."
    pm2 stop "$APP_NAME"
    pm2 delete "$APP_NAME"
fi

# Start the application
echo ""
echo "Starting application with PM2..."

# Create ecosystem file if it doesn't exist
if [ ! -f "ecosystem.config.js" ]; then
    print_info "Creating ecosystem.config.js..."
    cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: '${APP_NAME}',
    script: 'npm',
    args: 'start',
    env: {
      NODE_ENV: 'production',
      PORT: ${PORT}
    },
    instances: 1,
    exec_mode: 'fork',
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true
  }]
};
EOF
    print_success "ecosystem.config.js created"
fi

# Create logs directory
mkdir -p logs

# Start with PM2
NODE_ENV=$NODE_ENV pm2 start ecosystem.config.js

# Save PM2 process list
pm2 save

# Setup startup script (optional - requires sudo)
print_info "Setting up PM2 startup script..."
pm2 startup systemd -u $USER --hp $HOME || true

print_success "Deployment completed!"
echo ""
echo "================================================"
echo "Application: $APP_NAME"
echo "Port: $PORT"
echo "Environment: $NODE_ENV"
echo "================================================"
echo ""
echo "Useful commands:"
echo "  pm2 status          - Check application status"
echo "  pm2 logs $APP_NAME  - View application logs"
echo "  pm2 restart $APP_NAME - Restart application"
echo "  pm2 monit           - Monitor application"
echo ""
print_success "DOCiD Frontend is now running!"
echo ""
echo "Access your application at:"
echo "  http://localhost:$PORT (from server)"
echo "  https://docid.africapidalliance.org (from internet)"
echo ""