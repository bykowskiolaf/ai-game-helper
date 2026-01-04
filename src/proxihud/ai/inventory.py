from .. import utils

def analyze(client, img):
    prompt = """
    **ROLE:** ESO Market Expert & Build Crafter.
    **GOAL:** Evaluate the visible items.
    
    **OUTPUT FORMAT (Markdown):**
    # 🎒 LOOT APPRAISAL
    * **Best Item:** (Which visible item is most valuable/useful?)
    * **Action:** (Keep, Sell, or Deconstruct?)
    * **Note:** (Why is it good? e.g., "Good trait for tanks")
    """
    return utils.query_gemini(client, prompt, img)