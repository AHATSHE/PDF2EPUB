import logging
import logging.config
import os

if not os.path.exists('logs'):
    os.makedirs('logs')

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'logs/project.log'

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG, 
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()  
        ]
    )

    logging.getLogger('external_library').setLevel(logging.WARNING)