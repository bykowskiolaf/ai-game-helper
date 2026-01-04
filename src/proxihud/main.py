from .ui import GameHelperApp
from . import logger

def main():
    logger.setup_logging()
    try:
        app = GameHelperApp()
        app.mainloop()
    except Exception as e:
        import logging
        logging.critical(f"App crashed: {e}", exc_info=True)

if __name__ == "__main__":
    main()