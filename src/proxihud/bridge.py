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

        # Simple check to ensure we have data
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

            # Lists (New)
            "skills": _extract_list(content, "skills"),
            "quests": _extract_list(content, "quests"),

            # Stats (Flattened)
            # Regex finds ["magicka"] = 1234, globally, which works for SavedVars
            "stats_mag": _extract_num(content, "magicka"),
            "stats_hp": _extract_num(content, "health"),
            "stats_stam": _extract_num(content, "stamina"),

            # Complex Objects
            "equipment": _extract_equipment(content),
        }
        return data

    except Exception as e:
        logging.error(f"Bridge Read Error: {e}")
        return None

# --- Extraction Helpers ---

def _extract_str(text, key):
    # Lua format: ["key"] = "value",
    match = re.search(r'\s*\["' + key + r'"\]\s*=\s*"(.*?)",', text)
    return match.group(1) if match else "Unknown"

def _extract_num(text, key):
    # Lua format: ["key"] = 123,
    match = re.search(r'\s*\["' + key + r'"\]\s*=\s*(\d+),', text)
    return int(match.group(1)) if match else 0

def _extract_list(text, key):
    # Lua format: ["key"] = { "A", "B", "C" },
    # 1. Find the table block
    match = re.search(r'\s*\[' + f'"{key}"' + r'\]\s*=\s*\{(.*?)\},', text, re.DOTALL)
    if not match: return []

    # 2. Extract items inside quotes within that block
    return re.findall(r'"(.*?)"', match.group(1))

def _extract_equipment(text):
    # Extracts the equipment list items
    items = []
    # Find the equipment block
    eq_block_match = re.search(r'\["equipment"\]\s*=\s*\{(.*?)\},', text, re.DOTALL)
    if not eq_block_match:
        return []

    block = eq_block_match.group(1)
    # Find all name="X" and link="Y"
    names = re.findall(r'\["name"\]\s*=\s*"(.*?)",', block)
    links = re.findall(r'\["link"\]\s*=\s*"(.*?)",', block)

    # Zip them (safely)
    for i in range(len(names)):
        link_str = f" ({links[i]})" if i < len(links) else ""
        items.append(f"{names[i]}{link_str}")

    return items

def get_eso_saved_vars_path():
    return config.get_eso_saved_vars_path()