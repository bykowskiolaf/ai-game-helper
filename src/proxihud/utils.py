import json
import logging
from google import genai
from . import config

def clean_json_response(raw_text):
    try:
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        logging.warning(f"JSON Parsing failed: {e}")
        return None

def query_gemini(prompt, img):
    """
    Robust query function that handles:
    1. Client creation
    2. Key Rotation on 429 Errors (Quota Exceeded)
    """
    keys = config.get_api_keys()
    if not keys:
        raise ValueError("No API Keys configured")

    # Try as many times as we have keys (one full rotation)
    for attempt in range(len(keys) + 1):
        api_key = config.get_active_key()
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=config.AI_MODEL,
                contents=[prompt, img]
            )
            return response.text

        except Exception as e:
            error_str = str(e)
            # Check for Rate Limit (429) or Quota errors
            if "429" in error_str or "quota" in error_str.lower():
                logging.warning(f"Key exhausted (429/Quota). Rotating...")
                config.rotate_key()
                continue # Retry loop with new key
            
            # If it's a different error, crash out
            logging.error(f"Gemini API Call Failed: {e}")
            raise e
            
    raise Exception("All API Keys exhausted/rate-limited.")