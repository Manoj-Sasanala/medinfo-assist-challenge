"""Guide-data ingestion (Lane 1, Plan A): PyMuPDF per-page extraction.

Reads data/raw/*.pdf, writes:
  data/processed/corpus.json  - CT-01 chunks (1-based PHYSICAL pdf_page)
  docs/MANIFEST.md            - CT-06 source manifest (hash, page counts, empties)

Only allowlisted guide sources are indexed. Reference-only files are recorded
in the manifest but excluded from the corpus.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT_CORPUS = ROOT / "data" / "processed" / "corpus.json"
OUT_MANIFEST_JSON = ROOT / "data" / "processed" / "manifest.json"
OUT_FAISS = ROOT / "data" / "processed" / "embeddings.faiss"
OUT_MANIFEST = ROOT / "docs" / "MANIFEST.md"

# source_id -> (filename, document_title, index_this_source)
SOURCES: dict[str, tuple[str, str, bool]] = {
    "eating-and-diabetes-nih-08-5043": (
        "Eating_Diabetes_508.pdf",
        "What I Need to Know About Eating and Diabetes",
        True,
    ),
    "dia-ch01-reference": (
        "DIA_Ch01.pdf",
        "Diabetes in America Ch.1 (reference only, not indexed)",
        False,
    ),
}

CHUNK_CHARS = 900
OVERLAP = 120


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def page_chunks(page_no: int, text: str, prefix: str) -> list[dict]:
    text = re.sub(r"[ \t]+", " ", text).strip()
    if not text:
        return []
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    joined = "\n\n".join(paras)
    out, i, n = [], 0, 0
    while i < len(joined):
        piece = joined[i : i + CHUNK_CHARS]
        if len(piece) < 60 and out:
            out[-1]["text"] += " " + piece
            break
        n += 1
        out.append({"n": n, "text": piece.strip(), "page_no": page_no})
        if i + CHUNK_CHARS >= len(joined):
            break
        i += CHUNK_CHARS - OVERLAP
    return [{"cid": f"{prefix}-p{page_no:02d}-c{k['n']:02d}", **k} for k in out]


def main() -> int:
    manifest: list[dict] = []
    corpus: list[dict] = []
    for source_id, (filename, title, index) in SOURCES.items():
        path = RAW / filename
        if not path.exists():
            manifest.append(
                {
                    "source_id": source_id, "document_title": title,
                    "filename": filename, "sha256": "",
                    "page_count": 0, "extraction_status": "not_supplied",
                    "empty_pages": [], "indexed": False,
                    "notes": "File missing in data/raw/.",
                }
            )
            print(f"NOT_SUPPLIED {filename}", flush=True)
            continue
        doc = pymupdf.open(path)
        empty: list[int] = []
        pages = 0
        for i, page in enumerate(doc):
            pages += 1
            text = page.get_text()
            if not text.strip():
                empty.append(i + 1)
                continue
            if index:
                for c in page_chunks(i + 1, text, source_id[:6]):
                    corpus.append(
                        {
                            "chunk_id": c["cid"],
                            "source_id": source_id,
                            "document_title": title,
                            "filename": filename,
                            "pdf_page": c["page_no"],
                            "printed_page_label": None,
                            "section_title": None,
                            "text": c["text"],
                        }
                    )
        manifest.append(
            {
                "source_id": source_id, "document_title": title,
                "filename": filename, "sha256": sha256(path),
                "page_count": pages,
                "extraction_status": "ok" if not empty else "partial",
                "empty_pages": empty,
                "indexed": index,
                "notes": "Indexed." if index else "Reference only; excluded from corpus.",
            }
        )
        print(f"OK {filename} pages={pages} empty={empty} chunks={len(corpus)}", flush=True)
    OUT_CORPUS.write_text(json.dumps(corpus, indent=2), encoding="utf-8")
    OUT_MANIFEST_JSON.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    lines = ["# CT-06 Source Manifest", "", f"Sources: {len(manifest)}, indexed chunks: {len(corpus)}", ""]
    for m in manifest:
        lines += [
            f"## {m['source_id']}",
            f"- file: {m['filename']}",
            f"- sha256: {m['sha256']}",
            f"- pages: {m['page_count']} status={m['extraction_status']} empty={m['empty_pages']}",
            f"- notes: {m['notes']}", "",
        ]
    OUT_MANIFEST.write_text("\n".join(lines), encoding="utf-8")
    print(f"WROTE corpus={len(corpus)} manifest={len(manifest)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
