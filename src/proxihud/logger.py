import logging
import os
import sys
from . import config
from .updater import CURRENT_VERSION

def setup_logging():
    """Configures the logging system to write to AppData and console."""

    app_data = config.get_app_data_dir()
    log_file = os.path.join(app_data, "proxi_debug.log")

    # Load preference
    settings = config.load_settings()
    is_debug = settings.get("debug_logging", False)
    log_level = logging.DEBUG if is_debug else logging.INFO

    # Reset existing handlers if re-running
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.handlers = []

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(module)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.info("==========================================")
    logging.info(f"      PROXIHUD START (Debug: {is_debug})      ")
    logging.info(f"            Version: {CURRENT_VERSION}            ")
    logging.info("==========================================")
    logging.info(f"Log path: {log_file}")

def update_log_level(enable_debug):
    """Updates the logging level instantly without restart."""
    level = logging.DEBUG if enable_debug else logging.INFO
    logging.getLogger().setLevel(level)
    logging.info(f"Log level changed to: {'DEBUG' if enable_debug else 'INFO'}")