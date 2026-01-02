"""Configuration settings."""
from pathlib import Path

# Database
DATABASE_PATH = "zomato_orders.db"

# MBOX file path (can be overridden via command line)
MBOX_PATH = "Zomato.mbox"

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Data directory
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Logs
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
