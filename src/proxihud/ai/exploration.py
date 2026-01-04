from .. import utils

def analyze(client, img):
    prompt = """
    **ROLE:** Loremaster & Guide.
    **GOAL:** Provide context on the location or quest.
    
    **OUTPUT FORMAT (Markdown):**
    # 🌍 EXPLORATION
    * **Location:** (Where are we?)
    * **Tip:** (Look for skyshards, chests, or quest objectives here)
    """
    return utils.query_gemini(client, prompt, img)