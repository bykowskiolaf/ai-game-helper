import logging
from .. import config, utils, bridge
from . import query
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
    1. **READ THE HUD:** Prioritize reading text on screen (Quest Tracker, Death Recap, Tooltips).
    2. **SEARCH IF NEEDED:** If the user asks about specific mechanics, drop locations, or prices that are not on screen, **use Google Search** to find the latest UESP wiki data.
    3. **BE DIRECT:** No fluff. Give tactical, actionable advice.
    
    **SCENARIOS:**
    - **IF BOSS:** Search for "ESO [Boss Name] mechanics". Tell me what to interrupt or dodge.
    - **IF ITEM:** Search for "ESO [Item Name] build". Is it meta?
    - **IF QUEST:** Search the quest name. Where is the objective?

    **OUTPUT FORMAT:**
    Use Markdown. Use bolding. Keep it under 100 words.
    """

    # 4. EXECUTE
    logging.info("Sending Single-Shot Request to Gemini...")
    return query.query_gemini(system_prompt, img)