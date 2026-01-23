"""Logging utility."""
from loguru import logger
import sys

# Configure logger
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

logger.add(
    "logs/app_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level="DEBUG"
)

def get_logger(name: str):
    """Get a logger instance."""
    return logger.bind(name=name)

