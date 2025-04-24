#!/bin/bash

echo "Setting up lpg-ai-service..."

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run initial tests
pytest

echo "Setup complete! Run 'source .venv/bin/activate' to activate the virtual environment." 