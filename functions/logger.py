"""
Basic logging setup
Used to track app behavior and errors during execution.
Like print but more professional and flexible.
"""

import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO)

# Module-level logger instance
logger = logging.getLogger(__name__)


"""
# Example of usage:
from functions.logger import setup_logging, logger
setup_logging()
logger.info("Application started.")     # Normal information
logger.warning("Warning...")            # Something to check
logger.error("Error...")                # Something went wrong
"""