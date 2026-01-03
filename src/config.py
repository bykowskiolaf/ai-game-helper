import os
from dotenv import load_dotenv

load_dotenv()

TRIGGER_KEY = "f11"
EXIT_KEY = "f12"

def get_api_key():
    return os.getenv("GOOGLE_API_KEY")

def save_api_key(key):
    with open(".env", "w") as f:
        f.write(f"GOOGLE_API_KEY={key}")
    os.environ["GOOGLE_API_KEY"] = key