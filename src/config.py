import os
from dotenv import load_dotenv

# Load variables from .env if it exists
load_dotenv()

def get_api_key():
    """Returns the API Key from memory or environment"""
    return os.getenv("GOOGLE_API_KEY")

def save_api_key(key):
    """Saves the API key to .env and updates the environment"""
    with open(".env", "w") as f:
        f.write(f"GOOGLE_API_KEY={key}")
    os.environ["GOOGLE_API_KEY"] = key