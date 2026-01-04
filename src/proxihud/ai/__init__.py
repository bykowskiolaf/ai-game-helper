from google import genai
import logging
from .. import config, utils
from . import combat, inventory, death, skills, exploration

def analyze_image(img, user_prompt=None, history=[]):
    """
    Handles AI analysis with conversation history.
    """
    api_key = config.get_api_key()
    if not api_key: return "❌ API Key missing."

    try:
        client = genai.Client(api_key=api_key)

        # --- 1. CONSTRUCT HISTORY CONTEXT ---
        history_context = ""
        if history:
            history_context = "PREVIOUS CONVERSATION:\n"
            for msg in history:
                role = "User" if msg['role'] == "user" else "AI"
                history_context += f"{role}: {msg['text']}\n"
            history_context += "\nEND HISTORY.\n"

        # --- 2. HANDLE USER CHAT ---
        if user_prompt:
            prompt = f"""
            {history_context}
            
            **CURRENT TASK:**
            The user is asking a follow-up question about the CURRENT screen (image provided).
            User Question: "{user_prompt}"
            
            Answer efficiently based on the image and the previous context.
            """
            return utils.query_gemini(client, prompt, img)

        # --- 3. AUTO-ROUTER (If no text, just F11 scan) ---
        router_prompt = """
        Classify this ESO screen into ONE category:
        COMBAT, INVENTORY, SKILLS, DEATH, QUEST, OTHER.
        Return JSON: {"category": "COMBAT"}
        """
        
        # Use util to query
        raw_response = utils.query_gemini(client, router_prompt, img)
        
        # Use util to parse JSON
        data = utils.clean_json_response(raw_response)
        cat = data.get("category", "OTHER") if data else "OTHER"

        logging.info(f"Context Detected: {cat}")

        # Dispatch
        agents = {
            "COMBAT": combat,
            "INVENTORY": inventory,
            "DEATH": death,
            "SKILLS": skills,
            "OTHER": exploration,
            "QUEST": exploration
        }
        
        agent = agents.get(cat, exploration)
        return agent.analyze(client, img)

    except Exception as e:
        if "429" in str(e): return "⏳ Rate Limit."
        return f"Error: {e}"