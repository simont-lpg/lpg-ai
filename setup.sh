#!/bin/bash

# Exit on error
set -e

echo "Setting up haystack-rag-service..."

# Check Python version
if ! command -v python3.11 &> /dev/null; then
    echo "Python 3.11 is required but not found. Please install Python 3.11 and try again."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3.11 -m venv .venv

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[dev]"

# Run tests
echo "Running tests..."
make test

echo "Setup complete! You can now run the service with:"
echo "  make run"
echo "Or activate the virtual environment with:"
echo "  source .venv/bin/activate" 