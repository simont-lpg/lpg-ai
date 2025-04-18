FROM python:3.10-slim

WORKDIR /app

# Create and activate virtual environment
RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && python -m pip install --upgrade pip
ENV PATH="/opt/venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt requirements-dev.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]