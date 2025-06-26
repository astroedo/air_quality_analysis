"""
Basic logging setup
Used to track app behavior and errors during execution.
Like print but more professional and flexible.
(useful in FRONTEND API development and debugging)
"""

import logging

def setup_logging():
    # print timestamp, log level, and message
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# Module-level logger instance
logger = logging.getLogger(__name__)


"""
# Example of usage:
from functions.logger import setup_logging, logger
setup_logging()  # Set up logging configuration

logger.info("Application started.")             # Normal information
logger.warning("This is a warning.")            # Something to check
logger.error("Something went wrong!")           # Something went wrong

2025-06-19 14:55:02 - INFO - Application started.
2025-06-19 14:56:10 - WARNING - This is a warning.
2025-06-19 14:57:00 - ERROR - Something went wrong!
"""