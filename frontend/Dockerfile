FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Set PYTHONPATH to include the app directory
ENV PYTHONPATH="/app"

# Install uv, the Python package installer
RUN pip install uv

# Copy pyproject.toml and uv.lock to leverage Docker cache
COPY pyproject.toml uv.lock* /app/

# Install project dependencies
RUN uv sync --locked --no-cache

# Copy the frontend application code into the container
COPY ./frontend /app/frontend
COPY ./shared /app/shared

# Expose the port the app runs on
EXPOSE 8501

# Define the command to run the application
# Assuming your Streamlit app's entry point is frontend/src/app.py
CMD ["uv", "run", "streamlit", "run", "frontend/src/app.py", "--server.port=8501", "--server.address=0.0.0.0"] 