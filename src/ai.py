from google import genai
import config

def analyze_image(img):
    """Sends the image to Gemini and returns the advice text."""
    api_key = config.get_api_key()
    
    if not api_key:
        return "❌ Error: API Key is missing."

    try:
        client = genai.Client(api_key=api_key)
        
        prompt = """
        You are an expert Elder Scrolls Online (ESO) assistant.
        Look at this screenshot.
        
        STEP 1: CHECK CONTEXT
        - If this is NOT the game "Elder Scrolls Online" (e.g., a desktop, code editor, or browser), 
          STOP and strictly output: "❌ Not in game. Please open ESO."
        
        STEP 2: ANALYZE GAME
        - Only if it is ESO, identify the menu (Inventory, Skills, Death Recap, Open World).
        - Give one specific, high-impact tip based on the visible stats, items, or enemies.
        """
        
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[prompt, img]
        )
        return response.text

    except Exception as e:
        return f"❌ AI Error: {e}"