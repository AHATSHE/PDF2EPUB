import os
import logging

def setup_logging(log_file='logs/main.log', level=logging.DEBUG):
    # Ensure the logs directory exists
    logs_dir = os.path.dirname(log_file)
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    # Set logging level for external libraries if necessary
    logging.getLogger('fitz').setLevel(logging.WARNING)
