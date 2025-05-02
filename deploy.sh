#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to check if a file exists and warn if missing
check_file_exists() {
    local file="$1"
    local description="$2"
    if [ ! -f "$file" ]; then
        echo "Warning: $description file not found: $file"
        return 1
    fi
    return 0
}

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

# Step 4: Copy environment files
echo "📋 Copying environment files..."
# Check and copy backend environment
if check_file_exists "backend/.env.production" "Backend production environment"; then
    cp "backend/.env.production" "backend/.env"
    echo "Copied backend/.env.production → backend/.env"
fi

# Check and copy frontend environment
if check_file_exists "frontend/.env.production" "Frontend production environment"; then
    cp "frontend/.env.production" "frontend/.env"
    echo "Copied frontend/.env.production → frontend/.env"
fi

echo "✅ Deployment completed successfully!" 