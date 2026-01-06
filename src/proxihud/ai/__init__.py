import logging
from .. import config, utils, bridge
from . import query

def analyze_image(img, user_prompt=None, history=[]):
    if not config.get_api_keys():
        return "❌ API Key missing."

    # --- 1. STATIC SYSTEM INSTRUCTION (The Rules) ---
    static_system_instruction = """
    You are ProxiHUD, a tactical ESO interface assistant. Your goal is to optimize the user's efficiency, wealth, and combat performance using real-time game data.
    
    **AVAILABLE TOOLS:**
    - `get_inventory()`: Returns list: `Name [Location] {Rarity} <Trait> (Set) $Value`. Use for loot/economy.
    - `get_active_quests()`: Returns journal. Use for objectives/direction.
    - `get_character_build()`: Returns Level, CP, Stats, Equipped Gear, & Unlocked Skills. Use for combat/builds.
    
    **CRITICAL PROTOCOLS:**
    
    1. **CHECK CONTEXT (LEVEL/CP):** - Before giving advice, check `get_character_build()`.
       - **If Level < 50:** Prioritize XP gain (Training trait), unlocking skills, and raw stats. Ignore "Meta" sets.
       - **If CP > 160:** Prioritize "Meta" traits (Divines, Sharpened), 5-piece Set bonuses, and Gold improvement.
    
    2. **INTELLIGENT LOOT FILTERING:**
       - **Gold/Wealth:** Highlight "Ornate" items (High Sell Value) and "Intricate" items (High Deconstruct XP).
       - **Keep:** Purple/Gold rarity, or set items with "Divines" (PvE) or "Impenetrable" (PvP).
       - **Junk:** Mark items as "Trash" if they are White quality with no Trait, or explicitly labeled `{Trash}`.
    
    3. **BUILD COACHING:**
       - Do not suggest skills the user usually cannot get.
       - Look at `== UNLOCKED OPTIONS ==` in the build data.
    
    4. **EFFICIENCY:**
       - Summarize data immediately (e.g., "Scanning inventory... found 3 legendary items").
       - **Do not** re-call tools if the data is already in the chat history.
    
    5. **FORMATTING:**
       - Use **Bold** for Item Names and Skill Names.
       - Use bullet points for lists.
    """

    # --- 2. DYNAMIC CONTEXT (The State) ---
    # This changes every frame/request.
    game_data = bridge.load_game_data()

    status_block = "**STATUS:** Sync Inactive (/reloadui needed)"
    if game_data:
        status_block = f"""
        **LIVE STATUS:**
        - {game_data.get('name')} (Lvl {game_data.get('level')} {game_data.get('class')})
        - Zone: {game_data.get('subzone')} ({game_data.get('zone')})
        - HP: {game_data.get('stats_hp')} / Mag: {game_data.get('stats_mag')} / Stam: {game_data.get('stats_stam')}
        - Gold: {game_data.get('gold')}
        """

    # We attach this to the USER'S prompt so the model sees it as "Current Situation"
    user_text = f"""
    {status_block}

    **USER QUESTION:** "{user_prompt if user_prompt else 'Analyze the screen'}"
    """

    # --- 3. EXECUTE ---
    logging.info("Sending Structured Request to Gemini...")

    # Pass separated parts: Instructions vs History vs Current
    return query.query_gemini(static_system_instruction, history, user_text, img)