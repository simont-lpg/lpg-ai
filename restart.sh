#!/bin/bash

# Kill existing processes
echo "Killing existing processes..."
pkill -f "uvicorn app.main:app" || true
pkill -f "vite" || true

# Start backend server
echo "Starting backend server..."
cd backend && poetry run uvicorn app.main:app --reload --host localhost --port 8000 &
BACKEND_PID=$!

# Start frontend server
echo "Starting frontend server..."
cd frontend && npm run dev &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 