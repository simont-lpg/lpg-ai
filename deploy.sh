#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting deployment process..."

# Step 1: Change into project directory
echo "📁 Changing to project directory..."
cd "$(dirname "$0")"

# Step 2: Discard local modifications
echo "🗑️ Discarding local modifications..."
git fetch origin
git reset --hard origin/main
git clean -fd

# Step 3: Pull latest code
echo "⬇️ Pulling latest code..."
git pull origin main

echo "✅ Deployment completed successfully!" 