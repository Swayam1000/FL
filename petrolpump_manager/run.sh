#!/bin/bash

# Create necessary directories
mkdir -p logs data

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
echo "Starting FastAPI server..."
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload &

# Open the dashboard in the default browser
sleep 2
open "http://localhost:8000"

# Keep the script running
wait
