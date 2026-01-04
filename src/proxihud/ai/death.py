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
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, img]
    )
    return response.text