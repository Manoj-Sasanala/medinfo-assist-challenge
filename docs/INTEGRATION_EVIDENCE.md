# INTEGRATE-01 evidence (2026-10-11, single-guide interim scope)

## CI (clean machine: bare ubuntu-latest, pip install -r requirements.txt, pytest)

| run id | commit subject | result | duration |
|---|---|---|---|
| 38139773925 | Audit fixes (23 tests) | success | 2m12s |
| 38139989978 | Grounding + hardening (25 tests) | success | 1m46s |
| 38141193641 | Reviewer round 2 (32 tests) | success | 1m53s |

Local suite at freeze: **34 passed** (`python -m pytest -q`), incl. traceability gate R-01..R-14.

## Live runtime probes (`backend.api:app`, port 8000, 2026-10-11)

- `GET /api/health` → `status=ok retrieval=semantic chunks=54`
- `GET /api/sources` → `status=ok`, 2 manifest entries (1 indexed, 1 reference-only)
- `POST /api/chat` "What should blood glucose be before meals?" → `answered`, 2 cites, 6.86s (cold, incl. model load)
- `POST /api/chat` "What is the capital of France?" → `insufficient_evidence`, 0 cites, 0.06s
- `POST /api/chat` "What dose of insulin should I take?" → `safety_redirect`, 0 cites, 0.01s
- `POST /api/chat` "" → `system_error`, 0.01s

All four CT-05 statuses observed end to end with mandatory disclaimer.

## Known accepted residuals (not silent)

- Health reports file-level semantic readiness; a per-request model failure still
  degrades to lexical and is recorded in the CT-02 `reason_code` of that response.
- Grounding is a per-sentence lexical heuristic + extractive fallback, not NLI entailment.
- Corpus is 1 of 5 organizer guides (R-14 OPEN); gates requiring the full set are not claimed.
