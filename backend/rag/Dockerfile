FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy only necessary files for this service
COPY pyproject.toml uv.lock ./
COPY backend/rag ./backend/rag
COPY shared ./shared

# Install UV package manager
RUN pip install uv

# Install project dependencies
RUN uv pip install --no-cache-dir -e .

# Create storage and data directories
RUN mkdir -p /app/backend/rag/storage /app/backend/rag/data

# Expose port
EXPOSE 8001

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Start the service
CMD ["uvicorn", "backend.rag.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"] 