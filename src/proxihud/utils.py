import json
import logging
from google import genai
from google.genai import types
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
    1. Client creation per request (lightweight)
    2. Key Rotation on 429 Errors (Quota Exceeded)
    """
    keys = config.get_api_keys()
    if not keys:
        raise ValueError("No API Keys configured. Please check settings.")

    # Try as many times as we have keys (one full rotation)
    for _ in range(len(keys) + 1):
        api_key = config.get_active_key()
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=config.AI_MODEL,
                contents=[prompt, img]
            )
            return response.text

        except Exception as e:
            error_str = str(e).lower()

            # 429 = Too Many Requests / Quota Exceeded
            if "429" in error_str or "quota" in error_str or "resourceexhausted" in error_str:
                logging.warning(f"Key ...{api_key[-5:]} exhausted. Rotating...")
                if not config.rotate_key():
                    raise Exception("All API keys are currently exhausted.")
                continue # Retry loop with new key

            # Other errors (Auth, Server, etc.)
            logging.error(f"Gemini API Call Failed: {e}")
            raise e

    raise Exception("All API Keys exhausted or rate-limited.")