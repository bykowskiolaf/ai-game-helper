import logging
from .. import config, utils, bridge # <--- Import Bridge
from . import combat, inventory, death, skills, exploration

def analyze_image(img, user_prompt=None, history=[], settings={}):
    if not config.get_api_keys():
        return "❌ API Key missing. Please add in settings."

    # --- 1. BUILD CONTEXT ---
    persona = settings.get("persona", "Default")

    # FETCH GAME DATA
    game_data = bridge.load_game_data()

    context_str = ""
    if game_data:
        context_str = f"""
        **PLAYER CONTEXT (LIVE DATA):**
        - Character: {game_data.get('name')} (Level {game_data.get('level')} {game_data.get('race')} {game_data.get('class')})
        - Role: {game_data.get('role')}
        - Equipped Gear: {', '.join(game_data.get('equipment', [])[:10])}... (list truncated)
        """
    else:
        context_str = "**PLAYER CONTEXT:** No live data found. (Addon not synced? Type /reloadui in game)"

    system_instruction = ""
    if persona == "Sarcastic": system_instruction = "STYLE: You are a sarcastic, witty companion."
    elif persona == "Brief": system_instruction = "STYLE: Be extremely concise. Bullet points only."
    elif persona == "Pirate": system_instruction = "STYLE: You be a pirate! Yarr!"
    elif persona == "Helpful": system_instruction = "STYLE: You are overly supportive."

    # --- 2. HANDLE USER CHAT ---
    if user_prompt:
        history_context = ""
        if history:
            history_context = "PREVIOUS CONVERSATION:\n"
            for msg in history:
                role = "User" if msg['role'] == "user" else "AI"
                history_context += f"{role}: {msg['text']}\n"
            history_context += "\nEND HISTORY.\n"

        prompt = f"""
        {system_instruction}
        {context_str}
        
        {history_context}
        **CURRENT TASK:** Answer User Question about the image: "{user_prompt}"
        """
        return utils.query_gemini(prompt, img)

    # --- 3. AUTO-ROUTER ---
    logging.info("Auto-Routing...")

    # We inject the context into the router too, so it knows if we are looking at inventory
    router_prompt = f"""
    {context_str}
    Classify ESO screenshot: COMBAT, INVENTORY, SKILLS, DEATH, OTHER.
    Return JSON: {{"category": "COMBAT"}}
    """

    raw_response = utils.query_gemini(router_prompt, img)
    data = utils.clean_json_response(raw_response)
    category = data.get("category", "OTHER") if data else "OTHER"

    logging.info(f"Context: {category}")

    # Pass game_data to specific agents if they support it (optional refactor)
    # For now, we rely on the specific agent files or just general query if you merge them.
    if category == "COMBAT": return combat.analyze(img)
    elif category == "INVENTORY": return inventory.analyze(img)
    elif category == "DEATH": return death.analyze(img)
    elif category == "SKILLS": return skills.analyze(img)
    else: return exploration.analyze(img)