FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy only necessary files for this service
COPY pyproject.toml uv.lock ./
COPY frontend ./frontend
COPY shared ./shared

# Install UV package manager
RUN pip install uv

# Install project dependencies
RUN uv pip install --no-cache-dir -e .

# Expose Streamlit port
EXPOSE 8501

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Start the Streamlit app
CMD ["streamlit", "run", "frontend/src/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"] 