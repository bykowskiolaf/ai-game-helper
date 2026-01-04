def analyze(client, img):
    prompt = """
    **ROLE:** Veteran ESO Raid Leader.
    **GOAL:** Analyze the combat situation.
    
    **OUTPUT FORMAT (Markdown):**
    # ⚔️ COMBAT ANALYSIS
    * **Status:** (Health/Magicka/Stamina levels)
    * **Threat:** (Identify the most dangerous enemy or mechanic visible)
    * **Advice:** (One specific tactical instruction: e.g., "Block now", "Roll dodge", "Heal")
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, img]
    )
    return response.text