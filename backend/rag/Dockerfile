FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install uv, the Python package installer
RUN pip install uv

# Copy pyproject.toml and uv.lock to leverage Docker cache
COPY pyproject.toml uv.lock* /app/

# Install project dependencies
RUN uv sync --locked --no-cache

# Copy the rag application code into the container
COPY ./backend/rag /app/backend/rag
COPY ./shared /app/shared

# Expose the port the app runs on
EXPOSE 8001

# Define the command to run the application
# Assuming your FastAPI app's entry point is backend/rag/main.py and the app instance is named "app"
CMD ["uv", "run", "uvicorn", "backend.rag.main:app", "--host", "0.0.0.0", "--port", "8001"] 