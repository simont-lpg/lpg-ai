#!/bin/bash

# Function to print usage and exit
print_usage() {
    echo "Usage: $0 [dev|prod]"
    echo "  dev  - Start in development mode with live output"
    echo "  prod - Start in production mode with background processes and log files"
    exit 1
}

# Check if mode argument is provided
if [ $# -ne 1 ]; then
    print_usage
fi

# Get the base directory dynamically
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

MODE=$1

# Validate mode
if [ "$MODE" != "dev" ] && [ "$MODE" != "prod" ]; then
    echo "Error: Invalid mode. Must be either 'dev' or 'prod'"
    print_usage
fi

# Handle environment files
if [ "$MODE" = "prod" ]; then
    echo "Setting up production environment..."
    # Backend environment
    if [ -f "$BASE_DIR/backend/.env.production" ]; then
        cp "$BASE_DIR/backend/.env.production" "$BASE_DIR/backend/.env"
        echo "Copied backend/.env.production → backend/.env"
    else
        echo "Warning: backend/.env.production is missing"
    fi
    
    # Frontend environment
    if [ -f "$BASE_DIR/frontend/.env.production" ]; then
        echo "Copying frontend .env.production → .env"
        cp "$BASE_DIR/frontend/.env.production" "$BASE_DIR/frontend/.env"
    else
        echo "Warning: frontend/.env.production not found"
    fi
else
    echo "Setting up development environment..."
    if [ ! -f "$BASE_DIR/backend/.env" ]; then
        echo "Warning: backend/.env missing, please create from .env.example"
    fi
fi

# Kill existing processes based on mode
echo "Killing existing processes..."
if [ "$MODE" = "dev" ]; then
    pkill -f "uvicorn" || true
    pkill -f "vite" || true
else
    pkill -f "uvicorn" || true
fi

# Activate virtual environment from project root
echo "Activating virtual environment..."
source "$BASE_DIR/.venv/bin/activate" || { echo "Error: Could not activate virtual environment"; exit 1; }

if [ "$MODE" = "dev" ]; then
    # Dev mode: Start frontend dev server
    echo "Starting frontend in dev mode..."
    cd "$BASE_DIR/frontend" || { echo "Error: Could not change to frontend directory"; exit 1; }
    npm run dev &
    FRONTEND_PID=$!

    # Start backend in dev mode
    echo "Starting backend in dev mode..."
    cd "$BASE_DIR/backend" || { echo "Error: Could not change to backend directory"; exit 1; }
    uvicorn backend.app.main:app --reload --host $API_HOST --port $API_PORT &
    BACKEND_PID=$!

    # Wait for both processes
    wait $BACKEND_PID $FRONTEND_PID
else
    # Prod mode: Build frontend and start backend
    echo "Building frontend for production..."
    cd "$BASE_DIR/frontend" || { echo "Error: Could not change to frontend directory"; exit 1; }
    npm ci
    npm run build

    # Start backend in prod mode
    echo "Starting backend in production mode..."
    cd "$BASE_DIR/backend" || { echo "Error: Could not change to backend directory"; exit 1; }
    uvicorn backend.app.main:app --host 0.0.0.0 --port $API_PORT 