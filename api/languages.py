"""
Expose languages supported by googletrans, plus best-effort POS (Stanza) support info.
"""

from __future__ import annotations

from typing import Dict, List

from googletrans import LANGUAGES as GT_LANGUAGES

# Keep aliases in sync with api/pos.py
STANZA_ALIASES = {
    "jp": "ja",
    "zh-cn": "zh",
    "zh-tw": "zh-hant",
    "pt-br": "pt",
    "pt-pt": "pt",
}

# A conservative list of Stanza language codes known to have models.
# (This avoids importing stanza at import time; we don't want it to auto-download here.)
# Source: https://stanfordnlp.github.io/stanza/available_models.html (trimmed to common ones)
STANZA_LANGS = {
    "af",
    "ar",
    "bg",
    "ca",
    "cs",
    "da",
    "de",
    "el",
    "en",
    "es",
    "et",
    "eu",
    "fa",
    "fi",
    "fr",
    "ga",
    "gl",
    "he",
    "hi",
    "hr",
    "hu",
    "hy",
    "id",
    "it",
    "ja",
    "kk",
    "ko",
    "la",
    "lt",
    "lv",
    "mr",
    "nl",
    "no",
    "pl",
    "pt",
    "ro",
    "ru",
    "sk",
    "sl",
    "sr",
    "sv",
    "ta",
    "te",
    "th",
    "tr",
    "uk",
    "ur",
    "vi",
    "zh",
    "zh-hant",
}


def _normalize_pos_code(code: str) -> str:
    code = code.lower()
    return STANZA_ALIASES.get(code, code)


def get_languages() -> List[Dict[str, str | bool]]:
    """
    Build a list of language entries for the UI.

    Returns
    -------
    list of dict
        Each dict has:
        - code: str           # googletrans code to pass for translation
        - name: str           # human-readable name
        - pos_code: str       # normalized code we'd use for Stanza
        - pos_supported: bool # best-effort flag if we likely have a Stanza model
    """
    items: List[Dict[str, str | bool]] = []
    for code, name in GT_LANGUAGES.items():
        pos_code = _normalize_pos_code(code)
        pos_supported = pos_code in STANZA_LANGS
        items.append(
            {
                "code": code,
                "name": name.title(),
                "pos_code": pos_code,
                "pos_supported": pos_supported,
            }
        )
    # Sort alphabetically by name
    items.sort(key=lambda x: str(x["name"]))
    return items
