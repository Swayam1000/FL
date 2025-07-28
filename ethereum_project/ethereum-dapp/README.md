# Simple Ethereum DApp

This is a simple Ethereum DApp that demonstrates how to deploy and interact with a smart contract on the Sepolia testnet.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
- Copy `.env.example` to `.env`
- Fill in your Sepolia RPC URL (from Alchemy or Infura)
- Add your wallet's private key
- Add your Etherscan API key (for contract verification)

## Deployment

To deploy to Sepolia testnet:
```bash
npx hardhat run scripts/deploy.js --network sepolia
```

## Testing

To run tests:
```bash
npx hardhat test
```

## Local Development

To run a local Hardhat network:
```bash
npx hardhat node
```

Then deploy to local network:
```bash
npx hardhat run scripts/deploy.js --network localhost
```
