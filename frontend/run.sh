#!/bin/bash

# Frontend run script for DOCiD application

# Set script to exit on any error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if node is installed
if ! command -v node &> /dev/null; then
    print_message $RED "Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_message $RED "npm is not installed. Please install npm first."
    exit 1
fi

print_message $GREEN "Starting DOCiD Frontend..."

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    print_message $YELLOW "Installing dependencies..."
    npm install
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_message $YELLOW "Creating .env file from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_message $GREEN ".env file created. Please update it with your configuration."
    else
        print_message $YELLOW "No .env.example file found. Creating basic .env file..."
        echo "REACT_APP_API_URL=http://localhost:5000/api/v1" > .env
        echo "REACT_APP_BASE_URL=http://localhost:3000" >> .env
        print_message $GREEN ".env file created with default values."
    fi
fi

# Parse command line arguments
COMMAND=${1:-start}

case $COMMAND in
    start)
        print_message $GREEN "Starting development server..."
        npm run dev
        ;;
    build)
        print_message $GREEN "Building production bundle..."
        npm run build
        ;;
    test)
        print_message $GREEN "Running tests..."
        npm test
        ;;
    lint)
        print_message $GREEN "Running linter..."
        npm run lint
        ;;
    serve)
        print_message $GREEN "Building and serving production build..."
        npm run build
        npm start
        ;;
    prod)
        print_message $GREEN "Starting production server (requires build first)..."
        npm start
        ;;
    *)
        print_message $YELLOW "Usage: ./run.sh [start|build|test|lint|serve|prod]"
        print_message $YELLOW "  start  - Start development server (default)"
        print_message $YELLOW "  build  - Build production bundle"
        print_message $YELLOW "  test   - Run tests"
        print_message $YELLOW "  lint   - Run linter"
        print_message $YELLOW "  serve  - Build and serve production build"
        print_message $YELLOW "  prod   - Start production server (requires build first)"
        exit 1
        ;;
esac