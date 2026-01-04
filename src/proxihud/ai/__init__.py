from google import genai
import logging
import json
from .. import config

# Import our new agents
from . import combat, inventory, death, skills, exploration

def analyze_image(img):
    """
    Main Entry Point.
    1. Authenticates.
    2. Identifies Context (Router).
    3. Dispatches to the correct Agent.
    """
    api_key = config.get_api_key()
    if not api_key:
        return "❌ Error: API Key is missing."

    try:
        client = genai.Client(api_key=api_key)
        
        # --- STEP 1: ROUTER ---
        logging.info("Step 1: Identifying Context...")
        
        router_prompt = """
        Analyze this Elder Scrolls Online screenshot. 
        Classify the screen into exactly ONE of these categories:
        - "COMBAT": Active fighting, health bars visible, boss mechanics.
        - "INVENTORY": Looking at items, bank, or merchant.
        - "SKILLS": Looking at the skill tree or champion points.
        - "DEATH": Death recap screen (gray screen, "You Died").
        - "QUEST": Talking to an NPC or reading a quest journal.
        - "OTHER": Anything else.
        
        Return ONLY a raw JSON string like: {"category": "COMBAT"}
        """
        
        router_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[router_prompt, img]
        )
        
        # Parse JSON safely
        raw_text = router_response.text.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(raw_text)
            category = data.get("category", "OTHER")
        except:
            category = "OTHER"
            logging.warning(f"Router parsing failed, defaulting to OTHER. Raw: {raw_text}")

        logging.info(f"Context Detected: {category}")

        # --- STEP 2: DISPATCH TO AGENT ---
        # We pass the 'client' to the agent so it doesn't need to re-authenticate
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