"""Environment helpers for RealityCheck scripts."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


_DOTENV_LOADED = False


def _load_dotenv(env_path: Optional[Path] = None) -> None:
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return

    if env_path is None:
        env_path = Path(__file__).resolve().parent.parent / ".env"

    load_dotenv(env_path)
    _DOTENV_LOADED = True


@lru_cache(maxsize=1)
def get_openai_key() -> str:
    _load_dotenv()
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("❌ OPENAI_API_KEY missing – define in .env or GitHub Secrets.")
    return key


@lru_cache(maxsize=1)
def get_openai_client():
    from httpx import Client as HttpxClient
    from openai import OpenAI

    return OpenAI(api_key=get_openai_key(), http_client=HttpxClient())
