"""
Run script to start all REALM services.
"""
import os
import sys
import subprocess
import time
from pathlib import Path
import argparse

def start_gendoc_service():
    """Start the GenDoc service."""
    print("Starting GenDoc service...")
    subprocess.Popen([
        sys.executable, 
        "-m", "uvicorn", 
        "backend.gendoc.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ])
    print("GenDoc service started at http://localhost:8000")


def start_rag_service():
    """Start the RAG service."""
    print("Starting RAG service...")
    subprocess.Popen([
        sys.executable, 
        "-m", "uvicorn", 
        "backend.rag.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8001",
        "--reload"
    ])
    print("RAG service started at http://localhost:8001")


def start_frontend():
    """Start the Streamlit frontend."""
    print("Starting Streamlit frontend...")
    env = os.environ.copy()
    env["GENDOC_URL"] = "http://localhost:8000"
    env["RAG_URL"] = "http://localhost:8001"
    
    subprocess.Popen([
        sys.executable, 
        "-m", "streamlit", 
        "run", 
        "frontend/src/app.py",
        "--server.port", "8501"
    ], env=env)
    print("Streamlit frontend started at http://localhost:8501")


def main():
    """Main function to start all services."""
    parser = argparse.ArgumentParser(description="Start REALM services")
    parser.add_argument("--gendoc-only", action="store_true", help="Start only the GenDoc service")
    parser.add_argument("--rag-only", action="store_true", help="Start only the RAG service")
    parser.add_argument("--frontend-only", action="store_true", help="Start only the frontend")
    
    args = parser.parse_args()
    
    # Create necessary directories
    os.makedirs("backend/gendoc/storage", exist_ok=True)
    os.makedirs("backend/rag/storage", exist_ok=True)
    os.makedirs("backend/rag/data", exist_ok=True)
    
    # Start services based on arguments
    if args.gendoc_only:
        start_gendoc_service()
    elif args.rag_only:
        start_rag_service()
    elif args.frontend_only:
        start_frontend()
    else:
        # Start all services
        start_gendoc_service()
        time.sleep(1)  # Small delay to avoid port conflicts
        start_rag_service()
        time.sleep(1)  # Small delay to avoid port conflicts
        start_frontend()
    
    print("\nAll services started! Press Ctrl+C to stop.")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")


if __name__ == "__main__":
    main() 