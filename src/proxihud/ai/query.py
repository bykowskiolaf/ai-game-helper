from google import genai
from google.genai import types
from .. import config
import logging
from . import tools

def query_gemini(prompt, img):
    keys = config.get_api_keys()
    if not keys:
        raise ValueError("No API Keys configured. Please check settings.")


    # 3. Configure Request
    my_config = types.GenerateContentConfig(
        tools=tools.definitions,
        response_modalities=["TEXT"],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=False,
            maximum_remote_calls=2
        )
    )

    for _ in range(len(keys) + 1):
        api_key = config.get_active_key()
        try:
            client = genai.Client(api_key=api_key)

            response = client.models.generate_content(
                model=config.AI_MODEL,
                contents=[prompt, img],
                config=my_config
            )

            return response.text

        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str or "resourceexhausted" in error_str:
                logging.warning(f"Key ...{api_key[-5:]} exhausted. Rotating...")
                if not config.rotate_key():
                    raise Exception("All API keys are currently exhausted.")
                continue

            logging.error(f"Gemini API Call Failed: {e}")
            raise e

    raise Exception("All API Keys exhausted or rate-limited.")