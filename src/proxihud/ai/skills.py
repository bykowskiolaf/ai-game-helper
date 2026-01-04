from .. import utils

def analyze(client, img):
    prompt = """
    **ROLE:** ESO Theorycrafter.
    **GOAL:** Optimize the build.
    
    **OUTPUT FORMAT (Markdown):**
    # 🪄 BUILD CHECK
    * **Observation:** (What skill line or ability is focused?)
    * **Recommendation:** (Suggest a synergy or a passive to grab)
    """
    return utils.query_gemini(client, prompt, img)