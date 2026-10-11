# Frozen Acceptance Criteria (source: Notion Steps 1–9 + review rounds)

A requirement is DONE only when its mapped tests pass on CI (clean machine).
Adding a requirement without a mapped test fails the build
(see `tests/test_traceability.py`). Claims without a row here do not count.

| ID | Requirement (plan source) | Verified by |
|---|---|---|
| R-01 | One canonical entry point `backend.api:app`; README matches (9.4, Step 10) | test files import only `backend.*`; README quickstart |
| R-02 | Clean-install reproducibility: all imports declared (Step 8) | CI installs `requirements.txt` on bare image + full suite |
| R-03 | Ingestion never destroys a good corpus when PDFs are absent (Step 10 prereq) | test_ingestion_never_clobbers_corpus |
| R-04 | Embeddings refuse empty corpus (Plan A proof checkpoint) | test_embeddings_refuses_empty_corpus |
| R-05 | Semantic retrieval proven on gold queries; method recorded (CT-02, 07) | test_plan_a_gold_proof, test_search_endpoint_returns_pack |
| R-06 | Degraded paths never raise: missing/corrupt index, id mismatch, model failure, corrupt corpus (06 "explicit failures") | test_lexical_fallback_when_index_missing, test_corrupt_index_falls_back_to_lexical, test_mismatched_ids_fall_back_to_lexical, test_model_load_failure_falls_back_to_lexical, test_corrupt_corpus_fails_closed |
| R-07 | Diagnosis/dose requests redirect with zero citations (CT-03, 06 gates) | test_dose_phrasings_redirect, test_diagnosis_phrasings_redirect |
| R-08 | Emergency variants redirect (CT-03) | test_emergency_variants_redirect |
| R-09 | Prompt injection rejected in questions AND neutralized in passages (05/06) | test_prompt_injection_diagnose_redirects, test_prompt_injection_leak_stays_grounded, test_prompt_frames_passages_as_untrusted |
| R-10 | Every served sentence traces to cited passages or answer falls back to extractive quote (04/07 "no extra facts") | test_grounding_validator_on_live_answers, test_answer_with_extra_claim_is_ungrounded |
| R-11 | UI renders server content as text, never markup (05 release checks) | test_frontend_xss_safe |
| R-12 | Health/sources report honest CT-06 readiness incl. absent-raw case (CT-06) | test_health_readiness_fields, test_sources_endpoint_ct06, test_manifest_json_matches_corpus |
| R-13 | No secrets in repo (Step 8) | pre-push `git grep` scan for key/token patterns |
| R-14 | Five-guide corpus + labelled 90%/100% gates (01/06/07) | OPEN — blocked on organizer PDFs + terms |
