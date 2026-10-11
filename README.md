# MedInfo Assist Challenge

Practice hackathon workspace for MedInfo Assist — citation-first RAG chatbot over
organizer-supplied public-health PDF guides.

Current state: **single-PDF MVP** built on
"What I Need to Know About Eating and Diabetes"
(NIDDK, NIH Publication No. 08-5043, Oct 2007 — U.S. public domain).
Drop the real PDFs into `data/raw/` to replace the seed corpus.

## Quickstart

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:GOOGLE_API_KEY = "<your key>"   # Gemini answer generation (optional; extractive fallback otherwise)
python -m uvicorn app.main:app --port 8000
# open http://127.0.0.1:8000/
python -m pytest -q
```

## API

- `GET /api/health` — corpus stats
- `POST /api/search` `{query, top_k}` — retrieved evidence packs (CT-02)
- `POST /api/chat` `{question}` — grounded answer + citations or abstain/redirect

Contracts: `app/schemas.py` (CT-01 chunk, CT-02 evidence pack).
Safety: answers only from the allowlisted corpus, mandatory doc+page citation,
explicit abstain when unsupported, diagnosis/dose redirect, visible disclaimer.
