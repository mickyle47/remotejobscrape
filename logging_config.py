import logging
import logging.handlers
import os
import sys
from datetime import datetime

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logger
logger = logging.getLogger('remote_jobs_scraper')
logger.setLevel(logging.DEBUG)

# File handler with rotation
log_file = os.path.join('logs', 'scraper.log')
file_handler = logging.handlers.RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create formatters and add them to the handlers
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s'
)
console_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)

file_handler.setFormatter(file_formatter)
console_handler.setFormatter(console_formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Set up exception handling
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        # Call the default handler for KeyboardInterrupt
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # Log the exception with full traceback
    logger.error(
        "Uncaught exception:",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

# Install exception handler
sys.excepthook = handle_exception

# Log startup
logger.info(f"Logging started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Function to clean old log files
def clean_old_logs():
    try:
        log_dir = 'logs'
        if os.path.exists(log_dir):
            for file in os.listdir(log_dir):
                if file.startswith('scraper.log.') and file.split('.')[-1].isdigit():
                    file_path = os.path.join(log_dir, file)
                    try:
                        os.remove(file_path)
                        logger.debug(f"Cleaned old log file: {file}")
                    except Exception as e:
                        logger.warning(f"Could not remove old log file {file}: {str(e)}")
    except Exception as e:
        logger.error(f"Error cleaning old logs: {str(e)}")

# Clean old logs on startup
clean_old_logs()

# Prevent logging from propagating to the root logger
logger.propagate = False
