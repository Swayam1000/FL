import torch
from typing import Dict, List, Tuple
import flwr as fl
from utils import Net, load_data

def train(net, trainloader, epochs: int, device: torch.device):
    """Train the network on the training set."""
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(net.parameters())
    net.train()
    for _ in range(epochs):
        for images, labels in trainloader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(net(images), labels)
            loss.backward()
            optimizer.step()

def test(net, testloader, device: torch.device):
    """Validate the network on the entire test set."""
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
    return loss, accuracy

class FlowerClient(fl.client.NumPyClient):
    def __init__(self, cid: str, trainloader, valloader, device: str):
        self.cid = cid
        self.trainloader = trainloader
        self.valloader = valloader
        self.device = torch.device(device)
        self.net = Net().to(self.device)

    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in self.net.state_dict().items()]

    def set_parameters(self, parameters):
        params_dict = zip(self.net.state_dict().keys(), parameters)
        state_dict = {k: torch.tensor(v) for k, v in params_dict}
        self.net.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        self.set_parameters(parameters)
        train(self.net, self.trainloader, epochs=1, device=self.device)
        return self.get_parameters({}), len(self.trainloader.dataset), {}

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        loss, accuracy = test(self.net, self.valloader, self.device)
        return float(loss), len(self.valloader.dataset), {"accuracy": float(accuracy)}

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

if __name__ == "__main__":
    # Start client
    client = client_fn("0")  # Client ID 0
    fl.client.start_numpy_client(server_address="[::]:8080", client=client)
