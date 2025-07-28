import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import os

class BlockchainLogger:
    def __init__(self, ledger_path: str = None, blockchain_path: str = None):
        """Initialize the blockchain logger with file paths."""
        # Use absolute paths
        base_dir = Path(__file__).parent.parent
        self.ledger_path = Path(ledger_path) if ledger_path else base_dir / "logs/ledger.log"
        self.blockchain_path = Path(blockchain_path) if blockchain_path else base_dir / "logs/blockchain.log"
        self.ensure_directories()
        self.initialize_files()
        
    def clear_ledger(self):
        """Clear the ledger file."""
        with open(self.ledger_path, 'w') as f:
            f.write("# Federated Learning Training Ledger\n")
            f.write("# Format: {timestamp, round_num, clients, accuracy, loss}\n")
    
    def clear_blockchain(self):
        """Clear the blockchain file."""
        with open(self.blockchain_path, 'w') as f:
            f.write("# Blockchain Hashes for FL Training Rounds\n")
            f.write("# Format: {timestamp, round_num, hash, previous_hash}\n")
    
    def ensure_directories(self):
        """Ensure log directories exist."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.blockchain_path.parent.mkdir(parents=True, exist_ok=True)
    
    def initialize_files(self):
        """Initialize log files with headers if they don't exist."""
        if not self.ledger_path.exists():
            with open(self.ledger_path, 'w') as f:
                f.write("# Federated Learning Training Ledger\n")
                f.write("# Format: timestamp, round_num, clients, accuracy, loss\n")
        
        if not self.blockchain_path.exists():
            with open(self.blockchain_path, 'w') as f:
                f.write("# Blockchain Hashes for FL Training Rounds\n")
                f.write("# Format: timestamp, round_num, hash\n")
    
    def log_round(self, round_data: dict):
        """
        Log a training round to the ledger.
        
        Args:
            round_data: Dictionary containing round information with keys:
                - round_num: int
                - clients: List[str] (optional)
                - accuracy: float (optional)
                - loss: float (optional)
                - timestamp: float (optional, defaults to current time)
                - total_rounds: int (optional)
        """
        # Extract round_num from round_data
        round_num = round_data.get('round_num', 0)
        
        # Create a copy of the input to avoid modifying it
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'round_num': round_num,
            'clients': round_data.get('clients', []),
            'accuracy': round_data.get('accuracy'),
            'loss': round_data.get('loss')
        }
        
        # Add total_rounds if present
        if 'total_rounds' in round_data:
            log_entry['total_rounds'] = round_data['total_rounds']
        
        # Append to ledger
        with open(self.ledger_path, 'a') as f:
            f.write(f"{json.dumps(log_entry)}\n")
        
        # Add to blockchain
        self._add_to_blockchain(round_num, log_entry)
        
        return log_entry
    
    def _add_to_blockchain(self, round_num: int, data: Dict[str, Any]):
        """Add a block to the blockchain with the given data."""
        # Convert data to string and hash it
        data_str = json.dumps(data, sort_keys=True)
        block_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        # Get previous hash
        prev_hash = self._get_previous_hash()
        
        # Create block
        block = {
            "timestamp": datetime.utcnow().isoformat(),
            "round_num": round_num,
            "data_hash": block_hash,
            "previous_hash": prev_hash
        }
        
        # Append to blockchain
        with open(self.blockchain_path, 'a') as f:
            f.write(f"{json.dumps(block)}\n")
    
    def _get_previous_hash(self) -> str:
        """Get the hash of the last block in the blockchain."""
        try:
            with open(self.blockchain_path, 'r') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                if not lines:
                    return "0" * 64  # Genesis block
                last_block = json.loads(lines[-1])
                return last_block.get('data_hash', "0" * 64)
        except (FileNotFoundError, json.JSONDecodeError):
            return "0" * 64  # Genesis block
    
    def get_ledger(self) -> List[Dict]:
        """
        Read the entire ledger.
        
        Returns:
            List of ledger entries, each containing round information
        """
        ledger = []
        try:
            with open(self.ledger_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            entry = json.loads(line)
                            # Convert timestamp to float if it's a string
                            if isinstance(entry.get('timestamp'), str):
                                try:
                                    entry['timestamp'] = datetime.fromisoformat(entry['timestamp']).timestamp()
                                except (ValueError, TypeError):
                                    entry['timestamp'] = time.time()
                            ledger.append(entry)
                        except json.JSONDecodeError:
                            continue
            # Sort by round number
            ledger.sort(key=lambda x: x.get('round_num', 0))
        except FileNotFoundError:
            pass
        return ledger
    
    def get_blockchain(self) -> List[Dict[str, Any]]:
        """Get the blockchain hashes."""
        try:
            if not self.blockchain_path.exists():
                return []
                
            blockchain = []
            with open(self.blockchain_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            entry = json.loads(line)
                            blockchain.append(entry)
                        except json.JSONDecodeError:
                            continue
            return blockchain
        except Exception as e:
            print(f"Error reading blockchain: {e}")
            return []

# Create a global instance of the BlockchainLogger
blockchain_logger = BlockchainLogger()
