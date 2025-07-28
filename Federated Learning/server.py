import flwr as fl
from typing import Dict, List, Optional, Tuple, Union
import torch
from utils import Net, load_data

def get_evaluate_fn(testloader):
    """Return an evaluation function for server-side evaluation."""
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    def evaluate(
        server_round: int,
        parameters: fl.common.NDArrays,
        config: Dict[str, fl.common.Scalar],
    ) -> Optional[Tuple[float, Dict[str, fl.common.Scalar]]]:
        """Evaluate model on test set."""
        net = Net().to(device)
        params_dict = zip(net.state_dict().keys(), parameters)
        state_dict = {k: torch.tensor(v) for k, v in params_dict}
        net.load_state_dict(state_dict, strict=True)
        
        criterion = torch.nn.CrossEntropyLoss()
        correct, total, loss = 0, 0, 0.0
        net.eval()
        with torch.no_grad():
            for images, labels in testloader:
                images, labels = images.to(device), labels.to(device)
                outputs = net(images)
                loss += criterion(outputs, labels).item()
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        accuracy = correct / total
        return loss, {"accuracy": accuracy}
    
    return evaluate

def fit_config(server_round: int):
    """Return training configuration dict for each round."""
    return {
        "server_round": server_round,
        "local_epochs": 1,
    }

def main():
    # Load model and data
    net = Net()
    _, _, testloader = load_data()
    
    # Create strategy
    strategy = fl.server.strategy.FedAvg(
        fraction_fit=1.0,  # Sample 100% of available clients for training
        fraction_evaluate=0.5,  # Sample 50% of available clients for evaluation
        min_fit_clients=2,  # Minimum number of clients to be sampled for training
        min_evaluate_clients=2,  # Minimum number of clients to be sampled for evaluation
        min_available_clients=2,  # Minimum number of available clients
        evaluate_fn=get_evaluate_fn(testloader),  # The evaluation function
        on_fit_config_fn=fit_config,  # The fit configuration function
    )
    
    # Start Flower server
    fl.server.start_server(
        server_address="[::]:8080",
        config=fl.server.ServerConfig(num_rounds=3),
        strategy=strategy,
    )

if __name__ == "__main__":
    main()
