from dotenv import load_dotenv
import os

load_dotenv()

# Lazily initialize the OpenAI client so the app can start without an API key.
_api_key = os.getenv("OPENAI_API_KEY")
client = None
if _api_key:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=_api_key)
    except Exception:
        client = None


def ask_llm(prompt):
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not set. Set it to use the LLM features.")

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    return response.output_text