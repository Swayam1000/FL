# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains three main projects:

1. **petrolpump_manager** - A federated learning dashboard using Flower framework with FastAPI backend and web frontend
2. **ethereum_project/ethereum-dapp** - An Ethereum DApp with Hardhat development environment and React frontend
3. **modern-website** - A React + TypeScript website built with Vite

## Common Development Commands

### Federated Learning Dashboard (petrolpump_manager/)
```bash
# Start the complete application (recommended)
./run.sh

# Manual startup
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload

# Install Python dependencies
pip install -r requirements.txt

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Ethereum DApp (ethereum_project/ethereum-dapp/)
```bash
# Install dependencies
npm install

# Run tests
npx hardhat test

# Deploy to Sepolia testnet
npx hardhat run scripts/deploy.js --network sepolia

# Deploy to local network
npx hardhat node
npx hardhat run scripts/deploy.js --network localhost

# Frontend development (in frontend/ directory)
cd frontend
npm start
npm run build
npm test
```

### Modern Website (modern-website/)
```bash
# Development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Preview production build
npm run preview
```

## Architecture and Structure

### Federated Learning Dashboard
- **Backend**: FastAPI server with WebSocket support for real-time updates
- **Frontend**: Vanilla HTML/CSS/JS with Chart.js for visualizations
- **Core Components**:
  - `backend/app.py` - Main FastAPI application with API endpoints
  - `backend/server.py` - Flower federated learning server implementation
  - `backend/client.py` - Flower client implementation with PyTorch models
  - `backend/blockchain.py` - Blockchain logging for training auditability
  - `backend/utils.py` - Model definitions and data utilities
- **Data Flow**: Training sessions managed through REST API, real-time updates via WebSocket, blockchain logging for audit trail

### Ethereum DApp
- **Smart Contracts**: Solidity contracts in `contracts/` (SimpleStorage.sol, MetadataStorage.sol)
- **Development Environment**: Hardhat with Sepolia testnet configuration
- **Frontend**: React app using ethers.js for blockchain interaction
- **Deployment**: Scripts in `scripts/` directory, artifacts in `artifacts/`
- **Testing**: Hardhat test framework in `test/` directory

### Modern Website
- **Framework**: React 18 with TypeScript
- **Build System**: Vite with hot reload
- **Routing**: React Router DOM for navigation
- **Development**: ESLint for code quality

## Key Technical Details

### Environment Configuration
- **Ethereum DApp**: Requires `.env` file with SEPOLIA_RPC_URL, PRIVATE_KEY, and ETHERSCAN_API_KEY
- **Federated Learning**: Uses environment variables for blockchain logging and server configuration
- **Modern Website**: Vite configuration in `vite.config.ts` with dev server on port 3000

### Port Usage
- Federated Learning Dashboard: FastAPI on port 8000, Flower server on port 8080
- Modern Website: Vite dev server on port 3000
- Ethereum: Hardhat local network on default port 8545

### Data Storage
- **Federated Learning**: MNIST dataset in `data/MNIST/`, logs in `logs/` directory
- **Ethereum**: Compiled contracts in `artifacts/`, cache in `cache/`
- **Modern Website**: Build output in `dist/`

## Testing Approaches
- **Ethereum**: Use `npx hardhat test` for smart contract testing
- **React Frontend**: Use `npm test` or `react-scripts test`
- **Python Backend**: No specific test framework configured - consider adding pytest

## Development Workflows
- All projects use package managers (npm/pip) for dependency management
- Ethereum project supports both local and testnet deployment
- Federated learning dashboard includes blockchain logging for training auditability
- Modern website has TypeScript strict mode enabled with ESLint