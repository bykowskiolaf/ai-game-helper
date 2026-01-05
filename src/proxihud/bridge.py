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
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if "ProxiHUD_Data" not in content:
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
            "quest_dump": _extract_list(content, "quest_dump"),
            "skills_dump": _extract_list(content, "skills_dump"),

            # Equipment (Complex Object)
            "equipment": _extract_equipment(content),
        }
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

def _extract_equipment(text):
    items = []
    eq_block_match = re.search(r'\["equipment"\]\s*=\s*\{(.*?)\},', text, re.DOTALL)
    if not eq_block_match: return []

    block = eq_block_match.group(1)
    names = re.findall(r'\["name"\]\s*=\s*"(.*?)",', block)
    links = re.findall(r'\["link"\]\s*=\s*"(.*?)",', block)

    for i in range(len(names)):
        link_str = f" ({links[i]})" if i < len(links) else ""
        items.append(f"{names[i]}{link_str}")

    return items

def get_eso_saved_vars_path():
    return config.get_eso_saved_vars_path()