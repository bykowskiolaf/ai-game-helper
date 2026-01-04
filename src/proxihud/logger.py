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
            # CHANGED: mode='a' appends instead of overwriting
            logging.FileHandler(log_file, mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Add a separator to make reading easier
    logging.info("\n\n==========================================")
    logging.info("          PROXIHUD SESSION START          ")
    logging.info("==========================================")
    logging.info(f"Log path: {log_file}")