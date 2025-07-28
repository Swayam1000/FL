import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, random_split
import numpy as np

# Define a simple CNN model
class Net(nn.Module):
    def __init__(self) -> None:
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout(0.25)
        self.dropout2 = nn.Dropout(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)
        output = F.log_softmax(x, dim=1)
        return output

def load_data():
    """Load MNIST (training and test set)."""
    transform = transforms.Compose(
        [transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))]
    )
    
    # Download training data
    trainset = datasets.MNIST("./data", train=True, download=True, transform=transform)
    
    # Split training data into 10 partitions (one per client)
    num_clients = 10
    partition_size = len(trainset) // num_clients
    lengths = [partition_size] * num_clients
    lengths[-1] = len(trainset) - sum(lengths[:-1])  # Last partition gets the remainder
    
    datasets_list = random_split(trainset, lengths, torch.Generator().manual_seed(42))
    
    # Split each partition into train/val and create DataLoader
    trainloaders = []
    valloaders = []
    
    for ds in datasets_list:
        len_val = max(1, int(0.1 * len(ds)))  # 10% for validation
        len_train = len(ds) - len_val
        lengths = [len_train, len_val]
        ds_train, ds_val = random_split(ds, lengths, torch.Generator().manual_seed(42))
        
        trainloaders.append(DataLoader(ds_train, batch_size=32, shuffle=True))
        valloaders.append(DataLoader(ds_val, batch_size=32))
    
    # Prepare test set
    testset = datasets.MNIST("./data", train=False, transform=transform)
    testloader = DataLoader(testset, batch_size=32)
    
    return trainloaders, valloaders, testloader

def test(net, testloader, device: str = "cpu"):
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
    avg_loss = loss / len(testloader)
    
    return avg_loss, accuracy
