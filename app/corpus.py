"""Seed corpus loader. Single-PDF MVP: Eating and Diabetes (NIDDK 08-5043)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .schemas import Chunk

CORPUS_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "corpus.json"
ALLOWLIST = {"eating-and-diabetes-nih-08-5043"}


@lru_cache(maxsize=1)
def load_chunks() -> list[Chunk]:
    raw = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    chunks = [Chunk(**c) for c in raw]
    assert all(c.source_id in ALLOWLIST for c in chunks), "corpus outside allowlist"
    return chunks
