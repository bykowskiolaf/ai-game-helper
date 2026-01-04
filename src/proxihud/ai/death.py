from .. import utils

def analyze(client, img):
    prompt = """
    **ROLE:** Gentle Combat Coach.
    **GOAL:** Analyze the Death Recap.
    
    **OUTPUT FORMAT (Markdown):**
    # 💀 DEATH ANALYSIS
    * **Killer:** (What ability/enemy killed the player?)
    * **Mistake:** (Did they stand in AOE? Miss a block?)
    * **Tip:** (How to survive this next time)
    """
    return utils.query_gemini(client, prompt, img)