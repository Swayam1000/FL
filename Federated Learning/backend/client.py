import os
import sys
import time
import logging
from typing import Dict, List, Tuple, Optional
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
import flwr as fl
from flwr.common import (
    Code,
    EvaluateIns,
    EvaluateRes,
    FitIns,
    FitRes,
    GetParametersIns,
    GetParametersRes,
    Status,
    ndarrays_to_parameters,
    parameters_to_ndarrays,
)
from flwr.common.logger import log
from flwr.common.typing import GetParametersIns, Parameters

from utils import Net, load_data, test

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlowerClient(fl.client.NumPyClient):
    def __init__(self, cid: str, trainloader, valloader, device: str):
        self.cid = cid
        self.trainloader = trainloader
        self.valloader = valloader
        self.device = torch.device(device)
        self.net = Net().to(self.device)
        logger.info(f"Client {self.cid} initialized on device {self.device}")

    def get_parameters(self, config: Dict[str, str]) -> List[np.ndarray]:
        """Return the current local model parameters."""
        return [val.cpu().numpy() for _, val in self.net.state_dict().items()]

    def set_parameters(self, parameters: List[np.ndarray]) -> None:
        """Set the local model parameters using given parameters."""
        params_dict = zip(self.net.state_dict().keys(), parameters)
        state_dict = {k: torch.tensor(v).to(self.device) for k, v in params_dict}
        self.net.load_state_dict(state_dict, strict=True)

    def fit(
        self, parameters: List[np.ndarray], config: Dict[str, str]
    ) -> Tuple[List[np.ndarray], int, Dict]:
        """Train the model on the locally held training set."""
        # Set model parameters
        self.set_parameters(parameters)
        
        # Get training config
        epochs = int(config.get("epochs", 1))
        batch_size = int(config.get("batch_size", 32))
        
        # Train the model
        self.net.train()
        criterion = torch.nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(self.net.parameters(), lr=0.001)  # Explicit learning rate
        
        total_loss = 0.0
        correct = 0
        total = 0
        
        for _ in range(epochs):
            for images, labels in self.trainloader:
                images, labels = images.to(self.device), labels.to(self.device)
                optimizer.zero_grad()
                outputs = self.net(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                
                # Calculate training metrics
                total_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        # Calculate average loss and accuracy
        avg_loss = total_loss / len(self.trainloader)
        accuracy = correct / total
        
        logger.info(f"Client {self.cid} - Loss: {avg_loss:.4f}, Accuracy: {accuracy:.4f}")
        
        # Return updated model parameters and results
        return self.get_parameters({}), len(self.trainloader.dataset), {"loss": avg_loss, "accuracy": accuracy}

    def evaluate(
        self, parameters: List[np.ndarray], config: Dict[str, str]
    ) -> Tuple[float, int, Dict[str, float]]:
        """Evaluate the model on the local test set."""
        # Set model parameters
        self.set_parameters(parameters)
        
        # Evaluate the model
        self.net.eval()
        criterion = torch.nn.CrossEntropyLoss()
        correct, total, loss = 0, 0, 0.0
        
        with torch.no_grad():
            for images, labels in self.valloader:
                images, labels = images.to(self.device), labels.to(self.device)
                outputs = self.net(images)
                loss += criterion(outputs, labels).item()
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        accuracy = correct / total
        loss = loss / len(self.valloader)
        
        return float(loss), len(self.valloader.dataset), {"accuracy": float(accuracy), "loss": float(loss)}

def client_fn(cid: str) -> FlowerClient:
    """Create a Flower client."""
    # Load data
    trainloaders, valloaders, _ = load_data()
    
    # Create client
    return FlowerClient(
        cid=cid,
        trainloader=trainloaders[int(cid)],
        valloader=valloaders[int(cid)],
        device="cuda:0" if torch.cuda.is_available() else "cpu",
    )

def start_client(cid: str = "0", server_address: str = "127.0.0.1:8080"):
    """Start a single client."""
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    logger.info(f"Starting client {cid} connecting to {server_address}")
    try:
        client = client_fn(cid)
        fl.client.start_numpy_client(server_address=server_address, client=client)
        return True
    except Exception as e:
        logger.error(f"Client {cid} failed to start: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Flower Client")
    parser.add_argument("--cid", type=str, default="0", help="Client ID")
    parser.add_argument("--server-address", type=str, default="127.0.0.1:8080", 
                        help="Server address in the format host:port")
    args = parser.parse_args()
    
    success = start_client(cid=args.cid, server_address=args.server_address)
    if not success:
        sys.exit(1)
