import os
import sys
import json
import logging
from dotenv import load_dotenv

# --- APP INFO ---
APP_NAME = "ProxiHUD"
REPO_OWNER = "bykowskiolaf"
REPO_NAME = "ai-game-helper"

# --- AI CONFIG ---
AI_MODEL = "gemini-2.5-flash-lite" 

# --- DEFAULTS ---
DEFAULT_SETTINGS = {
    "opacity": 0.90,
    "hotkey_trigger": "f11",
    "hotkey_exit": "f12",
    "persona": "Default", 
    "geometry": "500x300+100+100"
}

# --- ENVIRONMENT STATE ---
def is_dev():
    return not getattr(sys, 'frozen', False)

# --- PATH HELPERS ---
def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except: base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def get_app_data_dir():
    if is_dev():
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    else:
        if os.name == 'nt':
            base = os.getenv('LOCALAPPDATA') or os.path.expanduser("~\\AppData\\Local")
        else:
            base = os.path.expanduser("~/.config")
        
        path = os.path.join(base, APP_NAME)
        os.makedirs(path, exist_ok=True)
        return path

# --- API KEY MANAGEMENT ---
_active_key_index = 0

def get_env_path():
    return os.path.join(get_app_data_dir(), ".env")

load_dotenv(get_env_path())

def get_api_keys():
    """Returns a list of keys found in the environment"""
    raw = os.getenv("GOOGLE_API_KEY", "")
    # Split by comma and strip whitespace
    return [k.strip() for k in raw.split(',') if k.strip()]

def get_active_key():
    """Returns the currently selected key"""
    keys = get_api_keys()
    if not keys: return None
    # Ensure index is within bounds (in case keys changed)
    global _active_key_index
    if _active_key_index >= len(keys): _active_key_index = 0
    return keys[_active_key_index]

def rotate_key():
    """Switches to the next available key"""
    global _active_key_index
    keys = get_api_keys()
    if not keys: return False
    
    prev = _active_key_index
    _active_key_index = (_active_key_index + 1) % len(keys)
    
    logging.info(f"Rotating API Key: {prev} -> {_active_key_index}")
    return True

def save_api_key(key_string):
    """Saves the raw string (can be comma separated)"""
    env_path = get_env_path()
    with open(env_path, "w") as f:
        f.write(f"GOOGLE_API_KEY={key_string}")
    os.environ["GOOGLE_API_KEY"] = key_string

# --- SETTINGS MANAGER ---
def get_settings_path():
    return os.path.join(get_app_data_dir(), "settings.json")

def load_settings():
    path = get_settings_path()
    if not os.path.exists(path): return DEFAULT_SETTINGS.copy()
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return {**DEFAULT_SETTINGS, **data} 
    except: return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(get_settings_path(), "w") as f:
            json.dump(settings, f, indent=4)
        logging.info("Settings saved.")
    except Exception as e:
        logging.error(f"Failed to save settings: {e}")