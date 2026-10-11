# MedInfo Assist Challenge (Plan A)

[![ci](https://github.com/Manoj-Sasanala/medinfo-assist-challenge/actions/workflows/ci.yml/badge.svg)](https://github.com/Manoj-Sasanala/medinfo-assist-challenge/actions/workflows/ci.yml)

Citation-first RAG chatbot over organizer-supplied public-health PDF guides.
One canonical app: **`backend.api:app`** (9.4 layout: `backend/ frontend/ contracts/ docs/`).

Current scope: **single-guide interim build** — "What I Need to Know About Eating
and Diabetes" (NIDDK, NIH 08-5043), 52 physical pages → 54 extracted chunks.
The five-organizer-PDF corpus required by Steps 1/6/7 is NOT yet complete;
remaining guides must be supplied with usage terms, then added to
`scripts/build_index.py` `SOURCES`. This scope reduction is recorded, not approved
as final acceptance.

## Quickstart (reproducible clean install)

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:GOOGLE_API_KEY = "<your key>"   # Gemini generation (optional; extractive fallback otherwise)
python -m uvicorn backend.api:app --port 8000
# open http://127.0.0.1:8000/
python -m pytest -q
```

The committed derived artifacts (`data/processed/corpus.json`, `manifest.json`,
`embeddings.faiss`) are used as-is, so no PDFs are needed to run or test.
Rebuild them only when the guide set changes and raw PDFs are present:

```powershell
python scripts/build_index.py        # PyMuPDF per-page extraction -> corpus + manifest
python scripts/build_embeddings.py   # all-MiniLM-L6-v2 + FAISS index
```

Both scripts fail safely (exit 1, existing artifacts untouched) when the
allowlisted PDFs are absent from `data/raw/`.

Raw PDFs stay local (`data/raw/*.pdf` is gitignored); committed derived
artifacts: `data/processed/corpus.json`, `manifest.json`, `embeddings.faiss`.

## API (CT-04 in, CT-05 out)

- `GET /api/health` — CT-06 readiness (`ok`/`not_ready`, chunk count, per-source manifest)
- `GET /api/sources` — CT-06 manifest entries with `raw_present` flags
- `POST /api/search` `{question}` — CT-02 evidence pack (retrieval method recorded)
- `POST /api/chat` `{question, history?}` — CT-03 safety → CT-02 retrieval → CT-05 answer

Contracts: `contracts/schemas.py` (CT-01..CT-06). Safety: allowlisted corpus only,
mandatory doc+page citation, abstain when unsupported, diagnosis/dose redirect,
visible disclaimer. UI renders all server content via `textContent` (XSS-safe).
