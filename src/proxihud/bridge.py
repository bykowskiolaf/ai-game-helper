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

        # PARSING STRATEGY:
        # Instead of a full Lua parser, we will extract the key sections we care about
        # using regex, which is faster and safer than eval().

        data = {
            "name": _extract_str(content, "name"),
            "race": _extract_str(content, "race"),
            "class": _extract_str(content, "class"),
            "level": _extract_num(content, "level"),
            "role": _extract_str(content, "role"),
            "equipment": _extract_equipment(content),
            # We can add inventory parsing later if needed, it can be huge
        }

        return data

    except Exception as e:
        logging.error(f"Bridge Read Error: {e}")
        return None

def _extract_str(text, key):
    # Lua format: ["key"] = "value",
    match = re.search(r'\s*\["' + key + r'"\]\s*=\s*"(.*?)",', text)
    return match.group(1) if match else "Unknown"

def _extract_num(text, key):
    # Lua format: ["key"] = 123,
    match = re.search(r'\s*\["' + key + r'"\]\s*=\s*(\d+),', text)
    return int(match.group(1)) if match else 0

def _extract_equipment(text):
    # Extracts the equipment list items
    # Looks for: ["name"] = "Item Name",
    items = []
    # Find the equipment block
    eq_block_match = re.search(r'\["equipment"\]\s*=\s*\{(.*?)\},', text, re.DOTALL)
    if not eq_block_match:
        return []

    block = eq_block_match.group(1)
    # Find all name="X" inside that block
    names = re.findall(r'\["name"\]\s*=\s*"(.*?)",', block)
    links = re.findall(r'\["link"\]\s*=\s*"(.*?)",', block)

    # Zip them (safely)
    for i in range(len(names)):
        items.append(f"{names[i]} ({links[i] if i < len(links) else ''})")

    return items

def get_eso_saved_vars_path():
    # Helper alias to keep this module self-contained if needed
    return config.get_eso_saved_vars_path()