import logging
import os
from django.conf import settings

logger = logging.getLogger('excel_exports')

def setup_export_logging():
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(settings.BASE_DIR, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Configure logging
    handler = logging.FileHandler(os.path.join(logs_dir, 'exports.log'))
    handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

def log_export(message, level='info'):
    if level == 'error':
        logger.error(message)
    elif level == 'warning':
        logger.warning(message)
    else:
        logger.info(message)