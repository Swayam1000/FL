import sys
print("Python path:", sys.path)

try:
    from backend.blockchain import blockchain_logger
    print("Successfully imported blockchain_logger")
except ImportError as e:
    print(f"Error importing blockchain_logger: {e}")

try:
    import uvicorn
    print(f"Uvicorn version: {uvicorn.__version__}")
except ImportError as e:
    print(f"Error importing uvicorn: {e}")
