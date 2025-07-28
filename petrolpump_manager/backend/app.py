import os
import sys
import time
import json
import subprocess
import uvicorn
import asyncio
import subprocess
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import logging
import signal
import psutil
from pathlib import Path
from threading import Thread

# Import blockchain logger
from . import blockchain

# Create blockchain logger instance
blockchain_logger = blockchain.BlockchainLogger()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
server_process = None
client_processes = []
TRAINING_IN_PROGRESS = False

app = FastAPI(title="Federated Learning Dashboard")

# Add request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
import os

# Get the absolute path to the frontend directory
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
static_dir = os.path.join(frontend_dir, "static")

# Log directory information for debugging
logger.info(f"Frontend directory: {frontend_dir}")
logger.info(f"Static directory: {static_dir}")
logger.info(f"Static directory exists: {os.path.exists(static_dir)}")

if os.path.exists(static_dir):
    logger.info(f"Files in static directory: {os.listdir(static_dir)}")
else:
    logger.error("Static directory does not exist!")

# Serve static files
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

# Serve index.html for the root path
@app.get("/", response_class=HTMLResponse)
async def read_root():
    index_path = os.path.join(static_dir, "index.html")
    logger.info(f"Looking for index.html at: {index_path}")
    
    if not os.path.exists(index_path):
        error_msg = f"Index file not found at {index_path}"
        logger.error(error_msg)
        return HTMLResponse(
            content=f"<h1>Error: {error_msg}</h1>",
            status_code=500
        )
    
    try:
        with open(index_path, "r") as f:
            content = f.read()
            # Fix any paths in the HTML if needed
            content = content.replace('href="/static/', 'href="/static/')
            content = content.replace('src="/static/', 'src="/static/')
            return HTMLResponse(content=content, status_code=200)
    except Exception as e:
        error_msg = f"Error reading index.html: {str(e)}"
        logger.error(error_msg)
        return HTMLResponse(
            content=f"<h1>Error: {error_msg}</h1>",
            status_code=500
        )

class TrainingConfig(BaseModel):
    num_rounds: int = 3
    num_clients: int = 3

# API Endpoints

@app.post("/api/train")
async def start_training(config: TrainingConfig, background_tasks: BackgroundTasks):
    """Start the federated learning training process."""
    global TRAINING_IN_PROGRESS, server_process, client_processes
    
    logger.info(f"Received training request: {config.num_rounds} rounds, {config.num_clients} clients")
    
    if TRAINING_IN_PROGRESS:
        logger.warning("Training is already in progress")
        raise HTTPException(status_code=400, detail="Training is already in progress")
    
    try:
        # Set training in progress flag
        TRAINING_IN_PROGRESS = True
        logger.info("Set TRAINING_IN_PROGRESS = True")
        
        # Start training in background
        logger.info("Adding training task to background tasks")
        background_tasks.add_task(
            start_training_process,
            num_rounds=config.num_rounds,
            num_clients=config.num_clients
        )
        
        logger.info("Background task added successfully")
        return {"status": "Training started", "rounds": config.num_rounds, "clients": config.num_clients}
        
    except Exception as e:
        logger.error(f"Error in start_training: {str(e)}", exc_info=True)
        TRAINING_IN_PROGRESS = False
        raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")

@app.get("/api/ledger")
async def get_ledger() -> List[Dict[str, Any]]:
    """Get the training ledger."""
    return blockchain_logger.get_ledger()

@app.get("/api/blockchain")
async def get_blockchain() -> List[Dict[str, Any]]:
    """Get the blockchain hashes."""
    return blockchain_logger.get_blockchain()

@app.get("/api/flower/status")
async def get_flower_status() -> Dict[str, Any]:
    """Get the current status of the Flower server."""
    global server_process, client_processes, TRAINING_IN_PROGRESS
    
    # Default values
    server_running = False
    flower_server_accessible = False
    clients_connected = 0
    current_round = 0
    total_rounds = 0
    
    # Check if server process is running
    if server_process and server_process.returncode is None:
        server_running = True
        
        # Try to connect to Flower server to verify it's actually running
        try:
            import requests
            response = requests.get("http://localhost:8081", timeout=2)
            if response.status_code == 200:
                flower_server_accessible = True
        except (requests.RequestException, ConnectionError):
            pass
        
        # Count running client processes
        clients_connected = len([p for p in client_processes if p.returncode is None])
        
        # Get current and total rounds from the ledger
        ledger = blockchain_logger.get_ledger()
        if ledger:
            current_round = len(ledger)
            # Get total_rounds from the first ledger entry or use a default
            total_rounds = ledger[0].get('total_rounds', 3) if ledger else 0
    
    return {
        "connected": server_running and flower_server_accessible,
        "server_running": server_running,
        "flower_accessible": flower_server_accessible,
        "clients_connected": clients_connected,
        "current_round": current_round,
        "total_rounds": total_rounds,
        "training_in_progress": TRAINING_IN_PROGRESS
    }

@app.get("/api/status")
async def get_status() -> Dict[str, Any]:
    """Get the current training status."""
    return {
        "training_in_progress": TRAINING_IN_PROGRESS,
        "server_running": server_process is not None and server_process.returncode is None,
        "clients_running": len([p for p in client_processes if p.returncode is None])
    }

@app.post("/api/stop")
async def stop_training():
    """Stop the training process."""
    global TRAINING_IN_PROGRESS, server_process, client_processes
    
    # Stop server
    if server_process and server_process.returncode is None:
        logger.info("Terminating server process...")
        server_process.terminate()
        try:
            await asyncio.wait_for(server_process.wait(), timeout=5)
        except asyncio.TimeoutError:
            logger.warning("Server process did not terminate gracefully, killing...")
            server_process.kill()
    
    # Stop clients
    for i, client in enumerate(client_processes):
        if client and client.returncode is None:
            logger.info(f"Terminating client {i}...")
            client.terminate()
            try:
                await asyncio.wait_for(client.wait(), timeout=5)
            except asyncio.TimeoutError:
                logger.warning(f"Client {i} did not terminate gracefully, killing...")
                client.kill()
    
    TRAINING_IN_PROGRESS = False
    server_process = None
    client_processes = []
    
    return {"status": "Training stopped"}

async def start_training_process(num_rounds: int = 3, num_clients: int = 3):
    """Start the federated learning training process."""
    global TRAINING_IN_PROGRESS, server_process, client_processes
    
    logger.info(f"Starting training process with {num_rounds} rounds and {num_clients} clients")
    
    try:
        # Clear previous ledger and blockchain for new training
        logger.info("Clearing ledger and blockchain")
        blockchain_logger.clear_ledger()
        blockchain_logger.clear_blockchain()
        
        # Log initial round with total rounds
        logger.info(f"Logging initial round with {num_rounds} total rounds")
        initial_round = {
            "round_num": 0,
            "total_rounds": num_rounds,
            "timestamp": time.time(),
            "clients": [],
            "accuracy": None,
            "loss": None
        }
        blockchain_logger.log_round(initial_round)
        
        # Start Flower server on port 8080
        server_port = 8080
        server_cmd = [
            sys.executable, "server.py",
            f"--port={server_port}",
            f"--rounds={num_rounds}",
            f"--clients={num_clients}"
        ]
        logger.info(f"Starting Flower server with command: {' '.join(server_cmd)}")
        
        # Start server process
        try:
            server_process = await asyncio.create_subprocess_exec(
                *server_cmd,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            logger.info(f"Server process created with PID: {server_process.pid}")
        except Exception as e:
            logger.error(f"Failed to start server process: {str(e)}", exc_info=True)
            TRAINING_IN_PROGRESS = False
            raise
        
        # Give server a moment to start
        logger.info("Waiting for server to start...")
        await asyncio.sleep(5)  # Increased delay to ensure server is ready
        
        # Check if server started successfully
        if server_process.returncode is not None:
            stdout, stderr = await server_process.communicate()
            logger.error(f"Server process failed to start. Return code: {server_process.returncode}")
            logger.error(f"Server stdout: {stdout.decode() if stdout else 'No output'}")
            logger.error(f"Server stderr: {stderr.decode() if stderr else 'No error'}")
            TRAINING_IN_PROGRESS = False
            raise RuntimeError(f"Server process failed to start with return code {server_process.returncode}")
        
        logger.info(f"Server process started successfully with PID: {server_process.pid}")
        
        # Start Flower clients
        client_processes = []
        server_address = f"127.0.0.1:{server_port}"
        
        for i in range(num_clients):
            client_cmd = [
                sys.executable, 
                "client.py", 
                f"--cid={i}",
                f"--server-address={server_address}"
            ]
            logger.info(f"Starting client {i} with command: {' '.join(client_cmd)}")
            
            try:
                client_process = await asyncio.create_subprocess_exec(
                    *client_cmd,
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                client_processes.append(client_process)
                logger.info(f"Client {i} started with PID: {client_process.pid}")
                
                # Small delay between client starts
                await asyncio.sleep(1.0)  # Increased delay to avoid connection issues
                
                # Check if client started successfully
                if client_process.returncode is not None:
                    stdout, stderr = await client_process.communicate()
                    logger.error(f"Client {i} failed to start. Return code: {client_process.returncode}")
                    logger.error(f"Client {i} stdout: {stdout.decode() if stdout else 'No output'}")
                    logger.error(f"Client {i} stderr: {stderr.decode() if stderr else 'No error'}")
                    await stop_training()
                    raise RuntimeError(f"Client {i} failed to start with return code {client_process.returncode}")
                    
            except Exception as e:
                logger.error(f"Error starting client {i}: {str(e)}", exc_info=True)
                await stop_training()
                raise
        
        logger.info(f"Started {num_clients} client processes")
        
        # Monitor processes
        logger.info("Starting process monitoring...")
        while True:
            # Check if server is still running
            if server_process.returncode is not None:
                logger.info(f"Server process ended with return code {server_process.returncode}")
                break
                
            # Check if all clients have finished
            all_clients_done = all(p.returncode is not None for p in client_processes)
            if all_clients_done:
                logger.info("All clients have finished")
                break
                
            # Log process status periodically
            running_clients = sum(1 for p in client_processes if p.returncode is None)
            logger.debug(f"Training in progress - {running_clients}/{num_clients} clients still running")
            
            await asyncio.sleep(5)  # Check every 5 seconds
        
        # Get any remaining output
        logger.info("Training completed, collecting final output...")
        
        if server_process.stdout:
            stdout, stderr = await server_process.communicate()
            if stdout:
                logger.info(f"Server stdout: {stdout.decode().strip()}")
            if stderr:
                logger.error(f"Server stderr: {stderr.decode().strip()}")
        
        for i, client in enumerate(client_processes):
            if client.stdout:
                stdout, stderr = await client.communicate()
                if stdout:
                    logger.info(f"Client {i} stdout: {stdout.decode().strip()}")
                if stderr:
                    logger.error(f"Client {i} stderr: {stderr.decode().strip()}")
        
        logger.info("Training completed successfully")
        
    except Exception as e:
        logger.error(f"Error in training process: {e}", exc_info=True)
        raise
        
    finally:
        logger.info("Cleaning up processes...")
        # Clean up any remaining processes
        if server_process and server_process.returncode is None:
            logger.info("Terminating server process...")
            server_process.terminate()
            try:
                await asyncio.wait_for(server_process.wait(), timeout=5)
                logger.info("Server process terminated successfully")
            except asyncio.TimeoutError:
                logger.warning("Server process did not terminate gracefully, killing...")
                server_process.kill()
        
        for i, client in enumerate(client_processes):
            if client and client.returncode is None:
                logger.info(f"Terminating client {i}...")
                client.terminate()
                try:
                    await asyncio.wait_for(client.wait(), timeout=5)
                    logger.info(f"Client {i} terminated successfully")
                except asyncio.TimeoutError:
                    logger.warning(f"Client {i} did not terminate gracefully, killing...")
                    client.kill()
        
        TRAINING_IN_PROGRESS = False
        logger.info("Set TRAINING_IN_PROGRESS = False")

if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs("../logs", exist_ok=True)
    
    # Start the FastAPI server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1
    )
