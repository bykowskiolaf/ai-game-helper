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
    """Retrieves combat build (Equipment, Skills, CP, Stats)."""
    logging.debug("Tool: 'get_character_build' called.")

    data = bridge.load_game_data()
    if not data: return "Data unavailable."

    # Grab all data points
    equipment = data.get('equipment_dump', [])
    active_skills = data.get('skills_dump', [])
    cp_stars = data.get('cp_dump', [])
    unlocked_skills = data.get('unlocked_dump', [])

    return f"""
    Class: {data.get('class', 'Unknown')}
    Role: {data.get('role', 'Unknown')}
    Stats: Mag={data.get('stats_mag')}, Stam={data.get('stats_stam')}, HP={data.get('stats_hp')}
    
    == EQUIPPED GEAR ==
    {chr(10).join(['- ' + s for s in equipment]) or "None"}

    == CHAMPION POINTS ==
    {chr(10).join(['- ' + s for s in cp_stars]) or "None"}

    == ACTIVE SKILLS ==
    {chr(10).join(['- ' + s for s in active_skills])}

    == UNLOCKED OPTIONS ==
    (Passives and other skills the player owns)
    {chr(10).join(['- ' + s for s in unlocked_skills])}
    """

definitions = [get_inventory, get_active_quests, get_character_build]