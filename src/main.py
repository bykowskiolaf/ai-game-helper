from ui import GameHelperApp
import logger

if __name__ == "__main__":
    logger.setup_logging()    
    try:
        app = GameHelperApp()
        app.mainloop()
    except Exception as e:
        import logging
        logging.critical(f"App crashed: {e}", exc_info=True)