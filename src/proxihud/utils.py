import json
import logging
from . import config

def clean_json_response(raw_text):
    """
    Cleans AI artifacts from JSON strings (e.g., ```json wrappers).
    Returns a dict or None if parsing fails.
    """
    try:
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        logging.warning(f"JSON Parsing failed: {e}. Raw Text: {raw_text}")
        return None

def query_gemini(client, prompt, img):
    """
    Standardized wrapper for calling the Gemini API.
    Uses the model defined in config.py.
    """
    try:
        response = client.models.generate_content(
            model=config.AI_MODEL,
            contents=[prompt, img]
        )
        return response.text
    except Exception as e:
        logging.error(f"Gemini API Call Failed: {e}")
        raise e