#!/bin/bash
set -euo pipefail

# Function to print usage and exit
print_usage() {
    echo "Usage: $0 [dev|prod]"
    echo "  dev  - Start in development mode with live output"
    echo "  prod - Start in production mode with background processes and log files"
    exit 1
}

# Function to handle cleanup on script exit
cleanup() {
    echo "Cleaning up..."
    # Only kill processes if they're still running
    if [ -n "${FRONTEND_PID:-}" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    if [ -n "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
}

# Set up trap for cleanup
trap cleanup EXIT

# Check if mode argument is provided
if [ $# -ne 1 ]; then
    print_usage
fi

# Get the base directory dynamically
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

MODE="$1"

# Validate mode
if [ "$MODE" != "dev" ] && [ "$MODE" != "prod" ]; then
    echo "Error: Invalid mode. Must be either 'dev' or 'prod'"
    print_usage
fi

# Kill existing processes based on mode
echo "Killing existing processes..."
if [ "$MODE" = "dev" ]; then
    pkill -f "uvicorn" || true
    pkill -f "vite" || true
else
    pkill -f "uvicorn" || true
fi

# Check if virtual environment exists, create if not
if [ ! -d "$BASE_DIR/.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$BASE_DIR/.venv" || { echo "Error: Could not create virtual environment"; exit 1; }
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$BASE_DIR/.venv/bin/activate" || { echo "Error: Could not activate virtual environment"; exit 1; }

if [ "$MODE" = "prod" ]; then
    echo "Setting up production environment..."
    
    # Build frontend
    echo "Building frontend for production..."
    cd "$BASE_DIR/frontend" || { echo "Error: Could not change to frontend directory"; exit 1; }
    npm ci || { echo "Error: npm ci failed"; exit 1; }
    npm run build || { echo "Error: npm build failed"; exit 1; }
    
    # Verify frontend build exists
    if [ ! -d "$BASE_DIR/frontend/dist" ]; then
        echo "Error: Frontend build failed - dist directory not found"
        exit 1
    fi
    
    # Start backend in production mode
    echo "Starting backend in production mode..."
    cd "$BASE_DIR" || { echo "Error: Could not change to base directory"; exit 1; }
    
    # Create logs directory if it doesn't exist
    mkdir -p "$BASE_DIR/logs"
    
    # Start backend with logging
    BASE_DIR="$BASE_DIR" uvicorn backend.app.main:app --host 0.0.0.0 --port 8003 > "$BASE_DIR/logs/backend.log" 2>&1 &
    BACKEND_PID=$!
    
    # Wait for backend to start and check if port is listening
    echo "Waiting for backend to start..."
    for i in {1..30}; do
        if nc -z localhost 8003; then
            echo "Backend started successfully with PID $BACKEND_PID"
            echo "Logs are being written to logs/backend.log"
            echo "Frontend is being served from frontend/dist"
            
            # Remove the cleanup trap since we want the backend to keep running
            trap - EXIT
            exit 0
        fi
        sleep 1
    done
    
    echo "Error: Backend failed to start. Check logs/backend.log for details."
    exit 1
else
    echo "Setting up development environment..."
    
    # Start frontend dev server
    echo "Starting frontend in dev mode..."
    cd "$BASE_DIR/frontend" || { echo "Error: Could not change to frontend directory"; exit 1; }
    npm run dev &
    FRONTEND_PID=$!
    
    # Start backend in dev mode
    echo "Starting backend in dev mode..."
    cd "$BASE_DIR" || { echo "Error: Could not change to base directory"; exit 1; }
    BASE_DIR="$BASE_DIR" uvicorn backend.app.main:app --reload --host "${API_HOST:-localhost}" --port "${API_PORT:-8000}" &
    BACKEND_PID=$!
    
    # Wait for both processes
    wait "$BACKEND_PID" "$FRONTEND_PID"
fi