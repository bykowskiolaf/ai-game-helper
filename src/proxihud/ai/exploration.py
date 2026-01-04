def analyze(client, img):
    prompt = """
    **ROLE:** Loremaster & Guide.
    **GOAL:** Provide context on the location or quest.
    
    **OUTPUT FORMAT (Markdown):**
    # 🌍 EXPLORATION
    * **Location:** (Where are we?)
    * **Tip:** (Look for skyshards, chests, or quest objectives here)
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, img]
    )
    return response.text