import os
from dotenv import load_dotenv

def get_openai_key():
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("❌ OPENAI_API_KEY missing – define in .env or GitHub Secrets.")
    return key
