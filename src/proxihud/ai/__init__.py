import logging
from .. import config, utils, bridge
from . import query

def analyze_image(img, user_prompt=None, history=[]):
    if not config.get_api_keys():
        return "❌ API Key missing."

    # --- 1. STATIC SYSTEM INSTRUCTION (The Rules) ---
    static_system_instruction = """
    You are ProxiHUD, an expert ESO companion.
    
    **AVAILABLE TOOLS:**
    - `get_inventory()`: Returns list format: `Name [Location] {Rarity} <Trait> (Set) $Value`. CALL THIS for loot/wealth.
    - `get_active_quests()`: CALL THIS for "What should I do?" or objective help.
    - `get_character_build()`: CALL THIS for combat advice/stats.

    **RULES:**
    1. **SUMMARIZE TOOLS:** If you call a tool, you MUST summarize the result (e.g., "I checked your bag, you have X").
    2. **CHECK HISTORY:** If the user asks about data you just retrieved, READ THE HISTORY. Do not call the tool again.
    3. **BE DIRECT:** Keep answers tactical and concise.
    4. **APPRAISE LOOT:** When asked about loot value, look for good rarity AND good traits (Divines, Impenetrable, Sharpened).
    5. **SET ADVICE:** If you see multiple items from the same Set (e.g. "Set: Julianos"), tell the user how many pieces they have.
    6. **JUNK DETECTION:** Items marked "{Trash}" or with $0g value should be recommended for sale/deletion.
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