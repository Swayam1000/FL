# Federated Learning Dashboard with Flower

A comprehensive dashboard for monitoring and managing federated learning training sessions using Flower, FastAPI, and a web-based interface.

## Features

- Start/stop federated learning training sessions
- Real-time monitoring of training progress
- Interactive charts for accuracy and loss metrics
- Detailed training ledger
- Blockchain-based logging for auditability
- Support for multiple clients
- Responsive web interface

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for cloning the repository)

## Installation

1. **Clone the repository** (or download the source code):
   ```bash
   git clone https://github.com/yourusername/federated-learning-dashboard.git
   cd federated-learning-dashboard
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Option 1: Using the run script (recommended)

```bash
./run.sh
```

This will:
1. Create necessary directories
2. Install Python dependencies
3. Start the FastAPI server
4. Open the dashboard in your default web browser

### Option 2: Manual startup

1. **Start the FastAPI server**:
   ```bash
   uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Access the dashboard**:
   Open your web browser and navigate to:
   ```
   http://localhost:8000
   ```

## Project Structure

```
.
├── backend/                  # Backend server code
│   ├── app.py               # FastAPI application
│   ├── server.py            # Flower server implementation
│   ├── client.py            # Flower client implementation
│   ├── utils.py             # Model and data utilities
│   └── blockchain.py        # Blockchain logging
├── frontend/                # Frontend files
│   └── static/              # Static files (HTML, CSS, JS)
│       ├── index.html      # Main dashboard
│       ├── style.css       # Styles
│       └── script.js       # Frontend logic
├── data/                    # Dataset storage
├── logs/                    # Log files
│   ├── ledger.log          # Training ledger
│   └── blockchain.log      # Blockchain hashes
├── requirements.txt         # Python dependencies
└── run.sh                  # Convenience script
```

## Usage

1. **Start a Training Session**:
   - Enter the number of training rounds
   - Specify the number of clients
   - Click "Start Training"

2. **Monitor Progress**:
   - View real-time accuracy and loss charts
   - Check the training ledger for detailed round information
   - Monitor blockchain hashes for auditability

3. **Stop Training**:
   - Click "Stop Training" to end the current session

## API Endpoints

- `GET /` - Dashboard interface
- `POST /api/train` - Start a training session
- `POST /api/stop` - Stop the current training session
- `GET /api/ledger` - Get training ledger data
- `GET /api/blockchain` - Get blockchain hashes
- `GET /api/status` - Get current training status

## Troubleshooting

- If you encounter port conflicts, ensure no other services are running on ports 8000 (FastAPI) or 8080 (Flower server)
- Check the console output for error messages
- Ensure all required Python packages are installed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Flower](https://flower.dev/) - The friendly federated learning framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- [PyTorch](https://pytorch.org/) - Deep learning framework
- [Chart.js](https://www.chartjs.org/) - Simple yet flexible JavaScript charting
- [Tailwind CSS](https://tailwindcss.com/) - A utility-first CSS framework
