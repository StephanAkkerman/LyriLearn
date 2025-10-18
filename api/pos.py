# api/pos.py
from functools import lru_cache

import stanza


@lru_cache(maxsize=16)
def get_nlp(lang: str) -> stanza.Pipeline:
    # processors: tokenize,pos,lemma,morph (mwt for some langs)
    return stanza.Pipeline(
        lang=lang, processors="tokenize,mwt,pos,lemma", use_gpu=False
    )


def annotate_line(text: str, lang: str) -> list[dict]:
    nlp = get_nlp(lang)
    doc = nlp(text)
    out = []
    for sent in doc.sentences:
        for w in sent.words:  # 'words' include MWT resolution
            out.append(
                {
                    "text": w.text,
                    "lemma": w.lemma or "",
                    "upos": w.upos,  # e.g., NOUN, VERB, ADJ
                    "xpos": w.xpos or "",
                    "feats": w.feats or "",  # e.g., Number=Sing|Tense=Past
                }
            )
    return out
