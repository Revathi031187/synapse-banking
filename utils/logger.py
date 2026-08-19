"""Logging utility."""
from loguru import logger
import logging
import sys
import io

# On Windows PowerShell 5.1 sys.stderr uses cp1252 — wrap with UTF-8 so emoji in log
# messages don't silently drop or crash the logger.
if hasattr(sys.stderr, 'buffer'):
    _stderr_sink = io.TextIOWrapper(
        sys.stderr.buffer, encoding='utf-8', errors='backslashreplace', line_buffering=True
    )
else:
    _stderr_sink = sys.stderr

# Configure logger
logger.remove()
logger.add(
    _stderr_sink,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=False,
)

logger.add(
    "logs/app_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level="DEBUG",
    encoding="utf-8",
)


class _InterceptHandler(logging.Handler):
    """Route all standard logging calls through loguru so agent logs appear in the terminal."""
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


# Install the intercept once when this module is first imported
logging.basicConfig(handlers=[_InterceptHandler()], level=logging.DEBUG, force=True)


def get_logger(name: str):
    """Get a logger instance."""
    return logger.bind(name=name)

