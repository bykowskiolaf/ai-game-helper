import json
import logging

def clean_json_response(raw_text):
    try:
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        logging.warning(f"JSON Parsing failed: {e}")
        return None

