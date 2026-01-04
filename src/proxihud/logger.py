import logging
import os
import sys
from . import config # Import config to use get_app_data_dir

def setup_logging():
    """Configures the logging system to write to AppData and console."""
    
    # Save logs in %LOCALAPPDATA%/ProxiHUD/proxi_debug.log
    app_data = config.get_app_data_dir()
    log_file = os.path.join(app_data, "proxi_debug.log")

    # Configure the logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(module)s: %(message)s",
        handlers=[
            # mode='a' appends to the log file
            logging.FileHandler(log_file, mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.info("==========================================")
    logging.info("          PROXIHUD SESSION START          ")
    logging.info("==========================================")
    logging.info(f"Log path: {log_file}")