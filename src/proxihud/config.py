import os
import sys
from dotenv import load_dotenv

load_dotenv()

# --- APP INFO ---
APP_NAME = "ProxiHUD"
REPO_OWNER = "bykowskiolaf"
REPO_NAME = "ai-game-helper"

# --- AI CONFIG ---
AI_MODEL = "gemini-2.5-flash" 

# --- HOTKEYS ---
TRIGGER_KEY = "f11"
EXIT_KEY = "f12"

# --- HELPER FUNCTIONS ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))

    return os.path.join(base_path, relative_path)

def get_api_key():
    return os.getenv("GOOGLE_API_KEY")

def save_api_key(key):
    with open(".env", "w") as f:
        f.write(f"GOOGLE_API_KEY={key}")
    os.environ["GOOGLE_API_KEY"] = key