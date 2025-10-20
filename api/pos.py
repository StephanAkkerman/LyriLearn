"""
Stanza-based POS/lemma annotator with lazy model download and caching.
"""

from functools import lru_cache

import stanza
from stanza.models.common.constant import lcode2lang

from .languages import _to_stanza_code


@lru_cache(maxsize=16)
def _pipeline(lang: str) -> stanza.Pipeline:
    """
    lang: googletrans-style code (e.g., 'id', 'zh-cn', 'pt-br').
    We normalize it to a Stanza code and build a cached pipeline.
    """
    code = _to_stanza_code(lang)

    # Optional guard: if Stanza doesn't know this code, raise early
    if code not in lcode2lang:
        # You can either raise, or fall back to English tokenizer:
        # return stanza.Pipeline(lang="en", processors="tokenize", tokenize_no_ssplit=True)
        raise ValueError(
            f"Stanza has no model for language code '{code}' (from '{lang}')"
        )

    try:
        return stanza.Pipeline(
            lang=code,
            processors="tokenize,mwt,pos,lemma",
            use_gpu=False,
            tokenize_no_ssplit=True,  # keep each lyric line as one sentence
        )
    except Exception:
        # Lazy download on first use
        stanza.download(code)
        return stanza.Pipeline(
            lang=code,
            processors="tokenize,mwt,pos,lemma",
            use_gpu=False,
            tokenize_no_ssplit=True,
        )


def annotate_line(text: str, lang: str) -> list[dict]:
    nlp = _pipeline(lang)
    doc = nlp(text)
    out: list[dict] = []
    for sent in doc.sentences:
        for w in sent.words:
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
    nlp = _pipeline(lang)
    doc = nlp(text)
    toks: list[str] = []
    for s in doc.sentences:
        for w in s.words:
            toks.append(w.text)
    return toks
