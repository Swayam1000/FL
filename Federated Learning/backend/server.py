import os
import sys
import time
import logging
from typing import Dict, List, Optional, Tuple, Union
import flwr as fl
from flwr.common import (
    EvaluateIns,
    EvaluateRes,
    FitIns,
    FitRes,
    MetricsAggregationFn,
    NDArrays,
    Parameters,
    Scalar,
    ndarrays_to_parameters,
    parameters_to_ndarrays,
)
from flwr.server.client_manager import ClientManager
from flwr.server.client_proxy import ClientProxy
import torch
import numpy as np

from blockchain import blockchain_logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SaveModelStrategy(fl.server.strategy.FedAvg):
    def __init__(
        self,
        min_fit_clients: int = 3,
        min_evaluate_clients: int = 3,
        min_available_clients: int = 3,
        **kwargs
    ) -> None:
        super().__init__(
            min_fit_clients=min_fit_clients,
            min_evaluate_clients=min_evaluate_clients,
            min_available_clients=min_available_clients,
            **kwargs
        )
        self.current_round = 0

    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple[ClientProxy, FitRes]],
        failures: List[Union[Tuple[ClientProxy, FitRes], BaseException]],
    ) -> Tuple[Optional[Parameters], Dict[str, Scalar]]:
        """Aggregate fit results and log to blockchain."""
        # Call parent's aggregate_fit
        aggregated_parameters, metrics = super().aggregate_fit(server_round, results, failures)
        
        if aggregated_parameters is not None:
            # Convert parameters to list of numpy arrays
            aggregated_ndarrays = parameters_to_ndarrays(aggregated_parameters)
            
            # Calculate weighted average of metrics
            accuracies = []
            losses = []
            client_ids = []
            
            for client, fit_res in results:
                if isinstance(fit_res.metrics, dict):
                    acc = fit_res.metrics.get("accuracy", 0.0)
                    loss = fit_res.metrics.get("loss", float('inf'))
                    accuracies.append(acc * fit_res.num_examples)
                    losses.append(loss * fit_res.num_examples)
                    client_ids.append(str(client.cid))
            
            total_examples = sum([fit_res.num_examples for _, fit_res in results])
            avg_accuracy = sum(accuracies) / total_examples if total_examples > 0 else 0.0
            avg_loss = sum(losses) / total_examples if total_examples > 0 else float('inf')
            
            # Log to blockchain
            blockchain_logger.log_round(
                round_num=server_round,
                clients=client_ids,
                accuracy=avg_accuracy,
                loss=avg_loss
            )
            
            logger.info(f"Round {server_round} completed with {len(results)} clients")
            logger.info(f"Round {server_round} average accuracy: {avg_accuracy:.4f}, average loss: {avg_loss:.4f}")
            
            # Add metrics to the returned metrics dictionary
            metrics = {"accuracy": avg_accuracy, "loss": avg_loss}
        
        return aggregated_parameters, metrics

def start_server(port: int = 8080, num_rounds: int = 3, num_clients: int = 3):
    logger.info(f"Starting Flower server on port {port} with {num_rounds} rounds and {num_clients} clients")
    
    strategy = SaveModelStrategy(
        min_fit_clients=num_clients,
        min_evaluate_clients=num_clients,
        min_available_clients=num_clients,
        evaluate_metrics_aggregation_fn=weighted_average,
        evaluate_fn=evaluate,
    )
    
    # Start server
    try:
        fl.server.start_server(
            server_address=f"0.0.0.0:{port}",
            config=fl.server.ServerConfig(num_rounds=num_rounds),
            strategy=strategy,
        )
    except Exception as e:
        logger.error(f"Failed to start Flower server: {str(e)}")
        raise

def weighted_average(metrics):
    """Aggregate metrics using weighted average."""
    accuracies = [num_examples * m["accuracy"] for num_examples, m in metrics]
    losses = [num_examples * m["loss"] for num_examples, m in metrics]
    examples = [num_examples for num_examples, _ in metrics]
    
    return {
        "accuracy": sum(accuracies) / sum(examples),
        "loss": sum(losses) / sum(examples),
    }

def evaluate(server_round: int, parameters: fl.common.NDArrays, config: Dict[str, fl.common.Scalar]):
    """Evaluate model on the server side."""
    # In a real implementation, you would evaluate the model on a test set here
    # For simplicity, we'll return dummy values
    return 0.0, {"accuracy": 0.0, "loss": 0.0}

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Flower Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    parser.add_argument("--rounds", type=int, default=3, help="Number of training rounds")
    parser.add_argument("--clients", type=int, default=3, help="Number of clients")
    
    args = parser.parse_args()
    
    logger.info(f"Starting Flower server on port {args.port} with {args.rounds} rounds and {args.clients} clients")
    try:
        start_server(port=args.port, num_rounds=args.rounds, num_clients=args.clients)
    except Exception as e:
        logger.error(f"Server failed: {str(e)}")
        sys.exit(1)
