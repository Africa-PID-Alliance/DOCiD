#!/bin/bash

# Script to restart Next.js development server with fresh cache

echo "Stopping any running Next.js processes..."
pkill -f "next dev" || true

echo "Clearing Next.js cache..."
rm -rf .next

echo "Clearing node_modules cache (optional)..."
# Uncomment the next line if you want to clear node_modules as well
# rm -rf node_modules/.cache

echo "Starting Next.js development server..."
npm run dev