import logging
from .. import config, utils
from . import combat, inventory, death, skills, exploration

def analyze_image(img, user_prompt=None, history=[], settings={}):
    # Check if we have any keys at all
    if not config.get_api_keys(): 
        return "❌ API Key missing. Please add in settings."

    # --- 1. DETERMINE PERSONA ---
    persona = settings.get("persona", "Default")
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
        {history_context}
        **CURRENT TASK:** Answer User Question about the image: "{user_prompt}"
        """
        # CHANGED: No client passed
        return utils.query_gemini(prompt, img)

    # --- 3. AUTO-ROUTER ---
    logging.info("Auto-Routing...")
    router_prompt = """
    Classify ESO screenshot: COMBAT, INVENTORY, SKILLS, DEATH, OTHER.
    Return JSON: {"category": "COMBAT"}
    """
    
    raw_response = utils.query_gemini(router_prompt, img)
    data = utils.clean_json_response(raw_response)
    category = data.get("category", "OTHER") if data else "OTHER"
    
    logging.info(f"Context: {category}")

    if category == "COMBAT": return combat.analyze(img)
    elif category == "INVENTORY": return inventory.analyze(img)
    elif category == "DEATH": return death.analyze(img)
    elif category == "SKILLS": return skills.analyze(img)
    else: return exploration.analyze(img)