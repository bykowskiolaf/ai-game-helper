import os
import re
import logging
from . import config

def load_game_data():
    """
    Reads the SavedVariables/ProxiHUD_Data.lua file and parses it into a Python dict.
    Returns None if file doesn't exist or is empty.
    """
    path = get_eso_saved_vars_path()

    if not os.path.exists(path):
        return None

    try:
        logging.debug(f"Bridge: Reading data from {path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if "ProxiHUD_Data" not in content:
            logging.debug("Bridge: File exists but 'ProxiHUD_Data' table missing.")
            return None

        data = {
            # Basic Info
            "name": _extract_str(content, "name"),
            "race": _extract_str(content, "race"),
            "class": _extract_str(content, "class"),
            "level": _extract_num(content, "level"),
            "role": _extract_str(content, "role"),

            # Location
            "zone": _extract_str(content, "zone"),
            "subzone": _extract_str(content, "subzone"),

            # Stats (Flattened)
            "stats_mag": _extract_num(content, "magicka"),
            "stats_hp": _extract_num(content, "health"),
            "stats_stam": _extract_num(content, "stamina"),

            # Currencies
            "gold": _extract_num(content, "gold"),
            "ap": _extract_num(content, "ap"),
            "telvar": _extract_num(content, "telvar"),

            # HEAVY DATA DUMPS (Lists)
            "inventory_dump": _extract_list(content, "inventory_dump"),
            "equipment_dump": _extract_list(content, "equipment_dump"),
            "quest_dump": _extract_list(content, "quest_dump"),
            "skills_dump": _extract_list(content, "skills_dump"),
            "unlocked_dump": _extract_list(content, "unlocked_dump"),
            "cp_dump": _extract_list(content, "cp_dump"),
        }

        logging.debug(f"Bridge: Parse success. Name={data['name']}, Zone={data['zone']}")

        return data

    except Exception as e:
        logging.error(f"Bridge Read Error: {e}")
        return None

# --- Extraction Helpers ---

def _extract_str(text, key):
    match = re.search(r'\s*\["' + key + r'"\]\s*=\s*"(.*?)",', text)
    return match.group(1) if match else "Unknown"

def _extract_num(text, key):
    match = re.search(r'\s*\["' + key + r'"\]\s*=\s*(\d+),', text)
    return int(match.group(1)) if match else 0

def _extract_list(text, key):
    match = re.search(r'\s*\[' + f'"{key}"' + r'\]\s*=\s*\{(.*?)\},', text, re.DOTALL)
    if not match: return []
    return re.findall(r'"(.*?)"', match.group(1))

def get_eso_saved_vars_path():
    return config.get_eso_saved_vars_path()