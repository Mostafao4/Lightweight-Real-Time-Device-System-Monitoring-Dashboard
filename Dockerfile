# Dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system deps (ping, gcc, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping netcat gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Default command (overridden in docker-compose)
CMD ["python", "run.py"]
