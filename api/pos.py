"""
Stanza-based POS/lemma annotator with lazy model download and caching.
Install: pip install stanza
"""

from __future__ import annotations

from functools import lru_cache

import stanza

# Normalize a few common aliases -> Stanza language codes
LANG_ALIASES = {
    "jp": "ja",
    "zh-cn": "zh",
    "zh-tw": "zh-hant",
    "pt-br": "pt",
    "pt-pt": "pt",
}


@lru_cache(maxsize=16)
def _pipeline(lang: str) -> stanza.Pipeline:
    code = LANG_ALIASES.get(lang.lower(), lang.lower())
    try:
        return stanza.Pipeline(
            lang=code,
            processors="tokenize,mwt,pos,lemma",
            use_gpu=False,
            tokenize_no_ssplit=True,  # keep your line as one "sentence"
        )
    except Exception:
        stanza.download(code)
        return stanza.Pipeline(
            lang=code,
            processors="tokenize,mwt,pos,lemma",
            use_gpu=False,
            tokenize_no_ssplit=True,
        )


def annotate_line(text: str, lang: str) -> list[dict]:
    """Return token dicts: text, lemma, upos, xpos, feats."""
    nlp = _pipeline(lang)
    doc = nlp(text)
    out: list[dict] = []
    for sent in doc.sentences:
        for w in sent.words:  # words: MWT-resolved tokens
            out.append(
                {
                    "text": w.text,
                    "lemma": w.lemma or "",
                    "upos": w.upos or "",
                    "xpos": w.xpos or "",
                    "feats": w.feats or "",
                }
            )
    return out


def tokenize_line(text: str, lang: str) -> list[str]:
    """
    Tokenize text into surface tokens using the same Stanza pipeline.
    Keeps line as a single sentence; returns tokens in order.
    """
    nlp = _pipeline(lang)
    doc = nlp(text)
    toks: list[str] = []
    for sent in doc.sentences:
        for w in sent.words:
            toks.append(w.text)
    return toks
