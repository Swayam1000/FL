import torch
from torchvision import datasets, transforms

def check_data():
    print("Downloading MNIST dataset...")
    
    # Define data transformations
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])
    
    # Download training data
    print("Downloading training data...")
    trainset = datasets.MNIST("./data", train=True, download=True, transform=transform)
    print(f"Training data downloaded. Number of samples: {len(trainset)}")
    
    # Download test data
    print("\nDownloading test data...")
    testset = datasets.MNIST("./data", train=False, download=True, transform=transform)
    print(f"Test data downloaded. Number of samples: {len(testset)}")
    
    # Check data shapes
    sample, label = trainset[0]
    print(f"\nSample data shape: {sample.shape}")
    print(f"Sample label: {label}")

if __name__ == "__main__":
    check_data()
