import logging
import os
import sys

def setup_logging():
    """Configures the logging system to write to a file and console."""
    
    # Determine where to save the log file
    if getattr(sys, 'frozen', False):
        # Running as EXE: Save next to the executable
        base_path = os.path.dirname(sys.executable)
    else:
        # Running as Code: Save in the project root
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    log_file = os.path.join(base_path, "proxi_debug.log")

    # Configure the logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(module)s: %(message)s",
        handlers=[
            # File Handler: Writes to proxi_debug.log (mode='w' overwrites each run)
            logging.FileHandler(log_file, mode='w', encoding='utf-8'),
            # Stream Handler: Still prints to console (useful for dev)
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.info("--- ProxiHUD Started ---")
    logging.info(f"Log path: {log_file}")