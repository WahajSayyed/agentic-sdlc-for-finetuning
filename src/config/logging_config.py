import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv
load_dotenv()

# Optional: define log directory
# LOG_DIR = os.path.join(os.getcwd(), "logs")
LOG_DIR = os.getenv("LOG_DIR")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Create a logger
logger = logging.getLogger("Agentic_SDLC")
logger.setLevel(logging.DEBUG)  # default log level

# File handler (with rotation)
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3)
file_handler.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)