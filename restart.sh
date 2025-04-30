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
    pkill -f "serve -s dist" || true
fi

# Activate virtual environment from project root
echo "Activating virtual environment..."
source "$BASE_DIR/.venv/bin/activate" || { echo "Error: Could not activate virtual environment"; exit 1; }

# Start backend
echo "Starting backend server..."
cd "$BASE_DIR/backend" || { echo "Error: Could not change to backend directory"; exit 1; }

if [ "$MODE" = "dev" ]; then
    # Dev mode: run in foreground with live output
    echo "Starting backend in dev mode (port 8000)..."
    uvicorn backend.app.main:app --reload --host localhost --port 8000 &
    BACKEND_PID=$!
else
    # Prod mode: run in background with log redirection
    echo "Starting backend in prod mode (port 8003)..."
    nohup uvicorn backend.app.main:app --host 0.0.0.0 --port 8003 > "$BASE_DIR/backend-prod.log" 2>&1 &
    BACKEND_PID=$!
fi

# Start frontend
echo "Starting frontend server..."
cd "$BASE_DIR/frontend" || { echo "Error: Could not change to frontend directory"; exit 1; }

if [ "$MODE" = "dev" ]; then
    # Dev mode: run in foreground with live output
    echo "Starting frontend in dev mode..."
    npm run dev &
    FRONTEND_PID=$!
else
    # Prod mode: build and serve
    echo "Building frontend for production..."
    npm install
    npm run build
    echo "Serving built frontend..."
    nohup npx serve -s dist -l 5173 > "$BASE_DIR/frontend-prod.log" 2>&1 &
    FRONTEND_PID=$!
fi

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 