from google import genai
import logging
import json
from .. import config
# Import the specialist modules (ensure these exist in src/proxihud/ai/)
from . import combat, inventory, death, skills, exploration

def analyze_image(img, user_prompt=None):
    """
    If user_prompt is provided, answers that specific question.
    Otherwise, auto-detects the context and uses a specialist agent.
    """
    api_key = config.get_api_key()
    if not api_key:
        return "❌ Error: API Key is missing."

    try:
        client = genai.Client(api_key=api_key)
        
        # --- PATH A: CUSTOM USER QUESTION ---
        if user_prompt:
            logging.info(f"Handling custom prompt: {user_prompt}")
            
            prompt = f"""
            **ROLE:** Expert Elder Scrolls Online Assistant.
            **USER QUESTION:** "{user_prompt}"
            **CONTEXT:** Analyze the screenshot to answer the user's question specifically.
            **OUTPUT:** Keep it short, direct, and helpful. Use Markdown for clarity.
            """
            
            # Using the main model for custom queries
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, img]
            )
            return response.text

        # --- PATH B: AUTO-ROUTER (Existing Logic) ---
        logging.info("Step 1: Identifying Context (Auto)...")
        
        router_prompt = """
        Analyze this Elder Scrolls Online screenshot. 
        Classify the screen into exactly ONE of these categories:
        - "COMBAT": Active fighting, health bars visible, boss mechanics.
        - "INVENTORY": Looking at items, bank, or merchant.
        - "SKILLS": Looking at the skill tree or champion points.
        - "DEATH": Death recap screen (gray screen, "You Died").
        - "QUEST": Talking to an NPC or reading a quest journal.
        - "OTHER": Anything else (map, loading screen, etc).
        
        Return ONLY a raw JSON string like: {"category": "COMBAT"}
        """
        
        router_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[router_prompt, img]
        )
        
        # Safe JSON parsing
        raw_text = router_response.text.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(raw_text)
            category = data.get("category", "OTHER")
        except:
            category = "OTHER"
            logging.warning(f"Router JSON parse failed. Raw: {raw_text}")

        logging.info(f"Context Detected: {category}")

        # Dispatch to Specialist Agent
        if category == "COMBAT": 
            return combat.analyze(client, img)
        elif category == "INVENTORY": 
            return inventory.analyze(client, img)
        elif category == "DEATH": 
            return death.analyze(client, img)
        elif category == "SKILLS": 
            return skills.analyze(client, img)
        else: 
            return exploration.analyze(client, img)

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return "⏳ Rate Limit. Please wait."
        logging.error(f"Analysis failed: {e}")
        return f"❌ AI Error: {e}"