# src/proxihud/ai/query.py
from google import genai
from google.genai import types
from .. import config
import logging
from . import tools
import io

def query_gemini(system_instruction, history, user_text, img):
    keys = config.get_api_keys()
    if not keys: raise ValueError("No API Keys configured.")

    function_tools = tools.definitions

    selectedModel = config.DEV_AI_MODEL if config.is_dev() else config.PROD_AI_MODEL

    my_config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=function_tools,
        response_modalities=["TEXT"],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=False,
            maximum_remote_calls=2
        )
    )

    contents = []
    for msg in history:
        role = "user" if msg['role'] == 'user' else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part(text=msg['text'])]
        ))

    # Convert Image
    if img.mode == 'RGBA':
        img = img.convert('RGB')

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()

    contents.append(types.Content(
        role="user",
        parts=[
            types.Part(text=user_text),
            types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=img_bytes))
        ]
    ))

    for i in range(len(keys) + 1):
        api_key = config.get_active_key()
        logging.debug(f"Gemini: Using Key ending in ...{api_key[-6:]}")

        try:
            client = genai.Client(api_key=api_key)

            response = client.models.generate_content(
                model=selectedModel,
                contents=contents,
                config=my_config
            )

            # --- DEBUGGING THE RESPONSE ---
            if response.candidates:
                candidate = response.candidates[0]
                logging.debug(f"Gemini: Finish Reason = {candidate.finish_reason}")

                # Check for content parts
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if part.function_call:
                            logging.debug(f"Gemini: Tool Call -> {part.function_call.name}")
                        if part.text:
                            logging.debug(f"Gemini: Text Part -> {part.text[:50]}...")
            else:
                logging.debug("Gemini: No candidates returned.")

            # --- ROBUST RETURN ---
            # If text is present, return it.
            if response.text and response.text.strip():
                return response.text

            # Fallback 1: If there are parts but no .text property (SDK quirk), try to join them
            if response.candidates and response.candidates[0].content.parts:
                manual_text = "".join([p.text for p in response.candidates[0].content.parts if p.text])
                if manual_text.strip():
                    return manual_text

            # Fallback 2: The model stayed silent
            logging.warning("Gemini: Returned empty response.")
            return "(The AI processed the data but returned no text. Check logs.)"

        except Exception as e:
            logging.error(f"API Error: {e}")
            if "429" in str(e) or "resource" in str(e).lower():
                config.rotate_key()
                continue
            raise e