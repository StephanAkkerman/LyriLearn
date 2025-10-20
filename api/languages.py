"""
Expose languages supported by googletrans, with POS support derived from
Stanza's official language registry.

- `code`      : googletrans code (what your frontend submits to the API)
- `name`      : human-readable language name (Title Case)
- `pos_code`  : best Stanza code candidate for POS tagging
- `pos_supported`: whether Stanza likely has a model for that code
- `rtl`       : right-to-left script hint (from Stanza constants)
"""

from __future__ import annotations

from typing import Dict, List

from googletrans import LANGUAGES as GT_LANGUAGES

# Import Stanza language constants (this does NOT download any models)
from stanza.models.common.constant import (
    RIGHT_TO_LEFT,  # set of stanza codes that are RTL
    lcode2lang,  # dict: stanza_code -> language name
    three_to_two_letters,  # dict: 'sme' -> 'se' etc.
)

# Map googletrans quirks -> Stanza codes
# (GT uses some BCP-47-ish tags and a few legacy codes)
GT_TO_STANZA_OVERRIDES: Dict[str, str] = {
    "zh-cn": "zh-hans",  # Chinese (Simplified)
    "zh-tw": "zh-hant",  # Chinese (Traditional)
    "pt-br": "pt",  # Portuguese (treat as 'pt' for POS)
    "pt-pt": "pt",
    "jw": "jv",  # old GT alias -> Javanese
    "nb": "nb",  # Bokmaal exists in Stanza mapping
    "no": "no",  # Norwegian (general)
}


def _to_stanza_code(gt_code: str) -> str:
    """
    Convert a googletrans language code to the best Stanza language code guess.
    Strategy:
      1) explicit overrides
      2) exact match in lcode2lang
      3) reduce BCP-47 like 'xx-YY' -> 'xx' if present in lcode2lang
      4) three_to_two_letters mapping (rare)
      5) fallback to lowercased gt_code (may not be supported)
    """
    code = gt_code.lower()

    # 1) explicit overrides
    if code in GT_TO_STANZA_OVERRIDES:
        return GT_TO_STANZA_OVERRIDES[code]

    # 2) exact stanza code
    if code in lcode2lang:
        return code

    # 3) reduce region/script subtags: e.g., "es-419" -> "es"
    if "-" in code:
        base = code.split("-", 1)[0]
        if base in lcode2lang:
            return base

    # 4) map some 3->2 letter codes if GT supplies a 3-letter code
    if code in three_to_two_letters:
        mapped = three_to_two_letters[code]
        if mapped in lcode2lang:
            return mapped

    # 5) fallback
    return code


def get_languages() -> List[Dict[str, str | bool]]:
    """
    Build a sorted list of language entries for the UI.
    """
    items: List[Dict[str, str | bool]] = []
    for gt_code, name in GT_LANGUAGES.items():
        pos_code = _to_stanza_code(gt_code)
        pos_supported = pos_code in lcode2lang
        rtl = pos_code in RIGHT_TO_LEFT
        items.append(
            {
                "code": gt_code,  # submit this back to your API
                "name": name.title(),
                "pos_code": pos_code,  # FYI for the UI (not required to submit)
                "pos_supported": pos_supported,  # show "(no POS)" if False
                "rtl": rtl,  # optional: can flip direction in UI
            }
        )
    items.sort(key=lambda x: str(x["name"]))
    return items
