# Handoff: build -> integration (Step 10 Plan A, single guide)

## What was built
- 9.4 layout: `backend/` (api, retrieve, safety, generate), `contracts/` (CT-01..CT-06 + fixtures/ reserved), `frontend/`, `docs/`, `scripts/`, `data/`, `tests/`.
- Ingestion: PyMuPDF per-PHYSICAL-page extraction of `Eating_Diabetes_508.pdf` (52pp, 3 image-only empties [2,4,6]) -> 54 CT-01 chunks. `DIA_Ch01.pdf` recorded reference-only, excluded from corpus (allowlist).
- Retrieval Plan A FIRST: all-MiniLM-L6-v2 + FAISS, threshold 0.30 calibrated on gold queries (proof in PIVOT_LOG). Lexical kept as degraded fallback only. No pivot.
- Chat: CT-03 -> CT-02 -> Gemini 2.5-flash (env key) or extractive -> CT-05 with mandatory disclaimer.

## Contracts
CT-01 chunk, CT-02 evidence pack (method recorded), CT-03 safety, CT-04 request, CT-05 response, CT-06 manifest. Fixtures live under `contracts/fixtures/` (none needed; real data used).

## Verify
`python -m pytest tests/test_plana.py -q` (5 tests) then `python -m uvicorn backend.api:app`.

## Known limits
- Single guide indexed (user-approved); 4 more organizer PDFs pending -> extend SOURCES + manifest to 5.
- Printed page labels not yet mapped (printed_page_label null); physical pdf_page is canonical.
- Old flat `app/` + `web/` + seed `corpus.json` superseded; remove after integration sign-off.
