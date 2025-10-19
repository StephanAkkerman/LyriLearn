"""
Minimal API to serve lyrics (LRC) and translations to a static frontend.
- /api/lyrics?title&artist → parse LRC and return structured lines
- /api/lyrics-with-translation?title&artist&src&dest → same + translations per line
- /api/translate (POST) → translate arbitrary text


Uses numpy-docstrings and built-in types.
"""

import os
import re

import syncedlyrics
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from googletrans import Translator
from pydantic import BaseModel

from .pos import annotate_line

# ---------- Config ----------
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")  # e.g., https://<user>.github.io


app = FastAPI(title="LyriLearn Minimal API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class POSReq(BaseModel):
    lyrics: str
    lang: str | None = None  # e.g., 'id'


class POSLine(BaseModel):
    t: float | None
    tokens: list[dict]


@app.post("/api/pos")
async def pos_endpoint(lang: str, body: POSReq) -> dict:
    lines = parse_lrc(body.lyrics)
    annotated = []
    for t, line in lines:
        tokens = annotate_line(line, lang)
        annotated.append(POSLine(t=t, tokens=tokens).model_dump())
    return {"lang": lang, "lines": annotated}


# ---------- Models ----------
class Line(BaseModel):
    t: float | None
    l2: str
    l1: str | None = None
    tokens: list[dict] | None = None  # <-- add this


class LyricsResponse(BaseModel):
    title: str
    artist: str
    lines: list[Line]


# ---------- Utils ----------
_lrc_pat = re.compile(r"^\[(\d{2}):(\d{2})(?:\.(\d{2}))?]\s*(.*)$")


def parse_lrc(lrc_text: str) -> list[tuple[float | None, str]]:
    """Parse LRC text to (time_sec, line_text).

    Parameters
    ----------
    lrc_text : str
    Raw LRC (timestamped) or plain lyrics text.

    Returns
    -------
    list[tuple[float | None, str]]
    Sequence of (time in seconds or None, text).
    """
    lines: list[tuple[float | None, str]] = []
    for raw in lrc_text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        m = _lrc_pat.match(raw)
        if m:
            mm, ss, cs, text = m.groups()
            t = int(mm) * 60 + int(ss) + (int(cs) / 100.0 if cs else 0.0)
            lines.append((t, text))
        else:
            lines.append((None, raw))
    return lines


async def translate_lines(texts: list[str], src: str, dest: str) -> list[str]:
    """Translate a list of lines while preserving order.

    Parameters
    ----------
    texts : list[str]
        Lines to translate.
    src : str
        Source language code (e.g., 'id').
    dest : str
        Target language code (e.g., 'en').


    Returns
    -------
    list[str]
        Translated lines in the same order.
    """
    # googletrans batches better with a single string; keep indexes via sentinel
    sentinel = "␞"  # record separator
    blob = sentinel.join(texts)
    async with Translator() as tr:  # uses your async form
        res = await tr.translate(blob, src=src, dest=dest)
    out = res.text.split(sentinel)
    # Fallback in case service collapsed newlines
    if len(out) != len(texts):
        out = res.text.splitlines()
        out += [""] * (len(texts) - len(out))
        out = out[: len(texts)]
    return out


# ---------- Routes ----------
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/lyrics", response_model=LyricsResponse)
async def get_lyrics_endpoint(title: str, artist: str) -> LyricsResponse:
    """Return parsed lyrics lines with timestamps (if present)."""
    try:
        lrc = syncedlyrics.search(f"{title} {artist}")
    except Exception as e:
        raise HTTPException(502, f"lyrics fetch failed: {e}")
    pairs = parse_lrc(lrc or "")
    return LyricsResponse(
        title=title, artist=artist, lines=[Line(t=t, l2=txt) for t, txt in pairs]
    )


@app.get("/api/lyrics-with-translation", response_model=LyricsResponse)
async def get_lyrics_with_translation(
    title: str, artist: str, src: str = "id", dest: str = "en"
) -> LyricsResponse:
    """Return lyrics with per-line translations."""
    data = await get_lyrics_endpoint(title=title, artist=artist)
    texts = [ln.l2 for ln in data.lines]
    try:
        tr = await translate_lines(texts, src=src, dest=dest)
    except Exception as e:
        raise HTTPException(502, f"translation failed: {e}")
    for ln, txt in zip(data.lines, tr):
        ln.l1 = txt
    return data


class TranslateBody(BaseModel):
    text: str
    src: str = "auto"
    dest: str = "en"


@app.post("/api/translate")
async def translate_body(body: TranslateBody) -> dict[str, str]:
    """Translate an arbitrary text block."""
    async with Translator() as tr:
        res = await tr.translate(body.text, src=body.src, dest=body.dest)
    return {"text": res.text}


@app.get("/api/lyrics-annotated", response_model=LyricsResponse)
async def get_lyrics_annotated(
    title: str, artist: str, lang: str, dest: str, pos: int = 1
) -> LyricsResponse:
    """
    Lyrics + translation + optional POS.
    We already know `lang` from the user (same as translation source).
    """
    data = await get_lyrics_with_translation(
        title=title, artist=artist, src=lang, dest=dest
    )
    if pos:
        for ln in data.lines:
            ln.tokens = annotate_line(ln.l2, lang)
    return data
