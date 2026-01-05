# src/proxihud/ai/tools.py
from .. import bridge

def get_inventory() -> str:
    """
    Retrieves the player's full inventory (Backpack and Bank).
    Call this when the user asks about specific items, loot, counts, or wealth.
    """
    data = bridge.load_game_data()
    # Check if we have the heavy dump available
    if not data or 'inventory_dump' not in data:
        return "Inventory data unavailable. User needs to /reloadui in ESO."

    # We join the list into a single string block for the AI to read
    return "\n".join(data['inventory_dump'])

def get_active_quests() -> str:
    """
    Retrieves the names of all active quests in the player's journal.
    Call this when the user asks 'What should I do?' or about current objectives.
    """
    data = bridge.load_game_data()
    if not data or 'quest_dump' not in data:
        return "Quest log is empty or unavailable."
    return "\n".join(data['quest_dump'])

def get_character_build() -> str:
    """
    Retrieves the player's combat build, including Class, Attributes, and Active Skills.
    Call this when the user asks for combat advice, rotation help, or build optimization.
    """
    data = bridge.load_game_data()
    if not data: return "Character data unavailable."

    return f"""
    Class: {data.get('class', 'Unknown')}
    Role: {data.get('role', 'Unknown')}
    Attributes: Magicka={data.get('stats_mag')}, Stamina={data.get('stats_stam')}, Health={data.get('stats_hp')}
    Skills Bar: {', '.join(data.get('skills_dump', []))}
    """

# Register the functions here so query.py can find them
definitions = [get_inventory, get_active_quests, get_character_build]