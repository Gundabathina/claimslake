"""
logger.py

Centralized logging setup for the ClaimsLake ingestion framework.

Uses Python's standard 'logging' module only - no external logging
dependency is justified at this project stage. Logs are written to both
the console (for interactive runs) and a log file under ingestion/logs/,
so a full ingestion history is available for review without needing a
dedicated log aggregation tool.
"""

import logging
import os

LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
)
LOG_FILE = os.path.join(LOG_DIR, "ingestion.log")

_configured = False


def get_logger(name: str = "claimslake.ingestion") -> logging.Logger:
    """Return a configured logger. Safe to call multiple times; handlers
    are attached only once to the shared 'claimslake' parent logger."""
    global _configured
    logger = logging.getLogger(name)

    if not _configured:
        os.makedirs(LOG_DIR, exist_ok=True)
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(formatter)

        root_logger = logging.getLogger("claimslake")
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        root_logger.propagate = False

        _configured = True

    return logger
