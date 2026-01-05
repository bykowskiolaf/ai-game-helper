import logging  # <--- Ensure this is imported
from .. import bridge

def get_inventory() -> str:
    """Retrieves the player's full inventory."""
    logging.debug("Tool: 'get_inventory' called.")

    data = bridge.load_game_data()
    if not data or 'inventory_dump' not in data:
        logging.warning("Tool: Inventory data missing.")
        return "Inventory unavailable."

    items = data['inventory_dump']
    logging.debug(f"Tool: Retrieved {len(items)} inventory items.")
    return "\n".join(items)

def get_active_quests() -> str:
    """Retrieves active quests."""
    logging.debug("Tool: 'get_active_quests' called.")

    data = bridge.load_game_data()
    if not data or 'quest_dump' not in data:
        logging.warning("Tool: Quest data missing.")
        return "Quest log empty."

    quests = data['quest_dump']
    logging.debug(f"Tool: Retrieved {len(quests)} active quests.")
    return "\n".join(quests)

def get_character_build() -> str:
    """Retrieves combat build."""
    logging.debug("Tool: 'get_character_build' called.")

    data = bridge.load_game_data()
    if not data: return "Data unavailable."

    build_info = f"Class: {data.get('class')}, Skills: {len(data.get('skills_dump', []))}"
    logging.debug(f"Tool: Build info found -> {build_info}")

    return f"""
    Class: {data.get('class', 'Unknown')}
    Role: {data.get('role', 'Unknown')}
    Attributes: Mag={data.get('stats_mag')}, Stam={data.get('stats_stam')}, HP={data.get('stats_hp')}
    Skills: {', '.join(data.get('skills_dump', []))}
    """

def get_golden_pursuits() -> str:
    """Retrieves active Golden Pursuits (Activity Finder campaigns)."""
    logging.debug("Tool: 'get_golden_pursuits' called.")

    data = bridge.load_game_data()
    if not data or 'golden_pursuits' not in data:
        logging.warning("Tool: Golden Pursuits data missing.")
        return "No active Golden Pursuits found."

    pursuits = data['golden_pursuits']

    if not pursuits:
        return "No active Golden Pursuits campaign currently running."

    logging.debug(f"Tool: Retrieved {len(pursuits)} pursuits.")
    return "\n".join(pursuits)

definitions = [get_inventory, get_active_quests, get_character_build, get_golden_pursuits]