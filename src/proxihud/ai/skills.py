def analyze(client, img):
    prompt = """
    **ROLE:** ESO Theorycrafter.
    **GOAL:** Optimize the build.
    
    **OUTPUT FORMAT (Markdown):**
    # 🪄 BUILD CHECK
    * **Observation:** (What skill line or ability is focused?)
    * **Recommendation:** (Suggest a synergy or a passive to grab)
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, img]
    )
    return response.text