#!/bin/bash

# Function to print usage and exit
print_usage() {
    echo "Usage: $0 [dev|prod]"
    echo "  dev  - Start in development mode"
    echo "  prod - Start in production mode"
    exit 1
}

# Check if mode argument is provided
if [ $# -ne 1 ]; then
    print_usage
fi

MODE=$1
BASE_DIR="/Users/simonlpg/Documents/lpg-ai"

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
    pkill -f "serve -s dist" || true
fi

# Start backend
echo "Starting backend server..."
cd "$BASE_DIR/backend" || { echo "Error: Could not change to backend directory"; exit 1; }

# Activate virtual environment
source .venv/bin/activate || { echo "Error: Could not activate virtual environment"; exit 1; }

if [ "$MODE" = "dev" ]; then
    nohup uvicorn backend.app.main:app --reload --host localhost --port 8000 > backend-dev.log 2>&1 &
    BACKEND_PID=$!
else
    nohup uvicorn backend.app.main:app --host 0.0.0.0 --port 8003 > backend-prod.log 2>&1 &
    BACKEND_PID=$!
fi

# Start frontend
echo "Starting frontend server..."
cd "$BASE_DIR/frontend" || { echo "Error: Could not change to frontend directory"; exit 1; }

if [ "$MODE" = "dev" ]; then
    nohup npm run dev > frontend-dev.log 2>&1 &
    FRONTEND_PID=$!
else
    nohup npx serve -s dist -l 5173 > frontend-prod.log 2>&1 &
    FRONTEND_PID=$!
fi

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 