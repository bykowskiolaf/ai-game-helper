import logging
from .. import config, utils, bridge
from . import query

def analyze_image(img, user_prompt=None, history=[]):
    """
    Single-Shot Analysis:
    Combines Visuals (Screen) + Tools (Deep Data) into one query.
    """
    if not config.get_api_keys():
        return "❌ API Key missing. Please add in settings."

    # 1. FETCH LIGHTWEIGHT CONTEXT (Always loaded)
    # We only load the 'Lite' data here. Heavy dumps (Inventory/Quests)
    # are hidden behind the Tools and only loaded if the AI requests them.
    game_data = bridge.load_game_data()

    player_context = ""
    if game_data:
        player_context = f"""
        **LIVE STATUS:**
        - Identity: {game_data.get('name')} (Level {game_data.get('level')} {game_data.get('class')})
        - Zone: {game_data.get('subzone')} (Zone: {game_data.get('zone')})
        - Vitals: {game_data.get('stats_hp')} HP / {game_data.get('stats_mag')} Mag / {game_data.get('stats_stam')} Stam
        - Wallet: {game_data.get('gold')} Gold
        """
    else:
        player_context = "**STATUS:** Data Sync Inactive. (User needs to /reloadui)"

    # 2. HISTORY
    chat_history = ""
    if history:
        chat_history = "PREVIOUS CHAT:\n" + "\n".join(
            [f"{'User' if msg['role'] == 'user' else 'AI'}: {msg['text']}" for msg in history[-4:]]
        )

    # 3. THE "MCP" SYSTEM PROMPT
    # We instruct the model to use the Python functions we defined in tools.py
    system_prompt = f"""
    You are ProxiHUD, an intelligent ESO companion.
    
    {player_context}
    
    {chat_history}

    **USER QUESTION:** "{user_prompt if user_prompt else 'Analyze the screen'}"

    **AVAILABLE DATA TOOLS:**
    - `get_inventory()`: CALL THIS for questions about loot, items, wealth, or "Do I have X?".
    - `get_active_quests()`: CALL THIS for "What should I do?", "Where is the quest?", or objective help.
    - `get_character_build()`: CALL THIS for combat advice, rotation help, or "Is my build good?".

    **INSTRUCTIONS:**
    1. **VISUALS FIRST:** Look at the screen image. If the answer is visible (e.g., "Boss is casting a spell", "Health is low"), answer immediately.
    2. **TOOLS SECOND:** If the answer requires hidden data (e.g., "Do I have enough materials?"), **DO NOT GUESS.** Call the appropriate tool.
    3. **BE DIRECT:** Keep answers under 50 words unless the user asks for a deep dive.

    **SCENARIOS:**
    - User: "What is in my bag?" -> Call `get_inventory()`.
    - User: "Help me fight this boss!" -> Analyze image for mechanics (Red circles, Cast bars).
    - User: "Where do I go next?" -> Call `get_active_quests()`.
    """

    # 4. EXECUTE
    logging.info("Sending Single-Shot Request to Gemini...")
    return query.query_gemini(system_prompt, img)