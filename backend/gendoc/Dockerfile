FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy only necessary files for this service
COPY pyproject.toml uv.lock ./
COPY backend/gendoc ./backend/gendoc
COPY shared ./shared

# Install UV package manager
RUN pip install uv

# Install project dependencies
RUN uv pip install --no-cache-dir -e .

# Create storage directory
RUN mkdir -p /app/backend/gendoc/storage

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Start the service
CMD ["uvicorn", "backend.gendoc.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 