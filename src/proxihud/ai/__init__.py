import logging
from .. import config, utils, bridge

def analyze_image(img, user_prompt=None, history=[], settings={}):
    """
    Single-Shot Analysis:
    Combines Game Data (Lua) + Visuals (Screen) into one fast query.
    """
    if not config.get_api_keys():
        return "❌ API Key missing. Please add in settings."

    # 1. FETCH LIVE GAME DATA (The "Ground Truth")
    game_data = bridge.load_game_data()

    player_context = ""
    if game_data:
        player_context = f"""
        **LIVE PLAYER DATA:**
        - Identity: {game_data.get('name')} (Level {game_data.get('level')} {game_data.get('race')} {game_data.get('class')})
        - Location: {game_data.get('subzone')} (Zone: {game_data.get('zone')})
        - Build: {game_data.get('stats_hp')} HP / {game_data.get('stats_mag')} Mag / {game_data.get('stats_stam')} Stam
        - Active Skills: {', '.join(game_data.get('skills', []))}
        - Current Quests: {', '.join(game_data.get('quests', [])[:5])} (Top 5)
        - Equipment: {', '.join(game_data.get('equipment', [])[:10])}
        """
    else:
        player_context = "**PLAYER DATA:** Unknown (Addon not synced). Rely strictly on the visual HUD."

    # 2. CONSTRUCT HISTORY
    # We keep it short to save tokens and reduce latency
    chat_history = ""
    if history:
        chat_history = "PREVIOUS CHAT:\n" + "\n".join(
            [f"{'User' if msg['role'] == 'user' else 'AI'}: {msg['text']}" for msg in history[-4:]]
        )

    # 3. THE "MASTER PROMPT"
    # This instructs Gemini to self-categorize and respond in one go.
    system_prompt = f"""
    You are ProxiHUD, an expert gaming companion for ESO (Elder Scrolls Online).
    
    {player_context}

    {chat_history}

    **USER QUESTION:** "{user_prompt if user_prompt else 'Analyze the screen'}"

    **INSTRUCTIONS:**
    1. **READ THE HUD:** Prioritize reading text on screen (Quest Tracker, Death Recap, Item Tooltips, Boss Health Bars).
    2. **DETECT CONTEXT:** Instantly decide if this is Combat, Inventory, Death, or Questing.
    3. **BE DIRECT:** No fluff. No personas. Give tactical, actionable advice based on what you see.
    
    **SCENARIOS:**
    - **IF DEATH RECAP:** Read the "Killing Blow" and "Hints" text. Explain exactly how to counter that specific mechanic.
    - **IF INVENTORY/ITEM:** Identify the item trait/set. Is it valuable? Is it meta for the player's class ({game_data.get('class') if game_data else 'Unknown'})?
    - **IF COMBAT:** Identify the enemy. Are there red AOE circles? Is Magicka/Stamina low?
    - **IF QUESTING:** Read the quest tracker text. Give a 1-sentence tip on that specific objective.

    **OUTPUT FORMAT:**
    Use Markdown. Use bolding for key terms. Keep it under 100 words unless asked for details.
    """

    # 4. EXECUTE
    logging.info("Sending Single-Shot Request to Gemini...")
    return utils.query_gemini(system_prompt, img)