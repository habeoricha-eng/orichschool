"""Génération pédagogique via l'API Groq (format compatible OpenAI)."""
import json
import os
import requests
import streamlit as st
from core.i18n import LANG_NAMES

URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"


class GenError(Exception):
    """Erreur de génération ; .code vaut 'no_key' ou 'failed'."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(detail or code)
        self.code = code
        self.detail = detail


def _secret(name: str, default: str = "") -> str:
    try:
        if name in st.secrets:
            val = st.secrets[name]
            if val:
                return str(val).strip()
    except Exception:
        pass
    return os.environ.get(name, default).strip()


SPECS = {
    "summary": (
        '{"title": str, "key_points": [str, ...6 to 10], '
        '"definitions": [{"term": str, "definition": str}], '
        '"formulas": [{"name": str, "latex": str}]}  (formulas may be empty)'
    ),
    "cards": '{"cards": [{"front": str, "back": str}, ...12 to 20]}',
    "quiz": (
        '{"questions": [{"question": str, "options": [4 strings], "answer": int index 0-3, '
        '"explanation": str}, ...8 to 10]}'
    ),
    "graph": (
        '{"nodes": [{"id": str, "label": str}, ...8 to 14], '
        '"edges": [{"from": id, "to": id, "label": str short}]}'
    ),
}


def generate(kind: str, text: str, lang: str) -> dict:
    key = _secret("GROQ_API_KEY")
    if not key:
        raise GenError("no_key", "Clé GROQ_API_KEY absente dans .streamlit/secrets.toml")

    model = _secret("GROQ_MODEL", DEFAULT_MODEL) or DEFAULT_MODEL
    language = LANG_NAMES.get(lang, "English")
    system = (
        f"You are a careful teacher. Work only from the course text provided. "
        f"Write in {language}. Keep technical terms, names and notations exactly as in the source. "
        f"Be clear and concrete. Reply with a single JSON object matching: {SPECS[kind]}"
    )

    try:
        r = requests.post(
            URL,
            timeout=90,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": text[:14000]},
                ],
            },
        )
        if r.status_code != 200:
            raise GenError("failed", f"HTTP {r.status_code} ({model}) : {r.text[:250]}")
        content = r.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except GenError:
        raise
    except Exception as e:
        raise GenError("failed", str(e)) from e