"""Traceability gate: every frozen requirement in docs/ACCEPTANCE.md must map to
at least one test that exists in the suite. This makes uncovered requirements
visible at build time instead of at review time.

It does not prove the tests are good — CI passing + reviewer judgment still do
that. It proves no requirement is silently untested.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# requirement -> [(test module, test function)]
REGISTRY: dict[str, list[tuple[str, str]]] = {
    "R-03": [("tests.test_robustness", "test_ingestion_never_clobbers_corpus")],
    "R-04": [("tests.test_robustness", "test_embeddings_refuses_empty_corpus")],
    "R-05": [("tests.test_plana", "test_plan_a_gold_proof"),
             ("tests.test_plana", "test_search_endpoint_returns_pack")],
    "R-06": [("tests.test_robustness", "test_lexical_fallback_when_index_missing"),
             ("tests.test_robustness", "test_corrupt_index_falls_back_to_lexical"),
             ("tests.test_robustness", "test_mismatched_ids_fall_back_to_lexical"),
             ("tests.test_robustness", "test_model_load_failure_falls_back_to_lexical"),
             ("tests.test_robustness", "test_corrupt_corpus_fails_closed")],
    "R-07": [("tests.test_safety_eval", "test_dose_phrasings_redirect"),
             ("tests.test_safety_eval", "test_diagnosis_phrasings_redirect")],
    "R-08": [("tests.test_safety_eval", "test_emergency_variants_redirect")],
    "R-09": [("tests.test_safety_eval", "test_prompt_injection_diagnose_redirects"),
             ("tests.test_safety_eval", "test_prompt_injection_leak_stays_grounded"),
             ("tests.test_robustness", "test_prompt_frames_passages_as_untrusted")],
    "R-10": [("tests.test_robustness", "test_grounding_validator_on_live_answers"),
             ("tests.test_robustness", "test_answer_with_extra_claim_is_ungrounded"),
             ("tests.test_robustness", "test_nli_entailment_calibration"),
             ("tests.test_robustness", "test_nli_rejects_extra_claim_accepts_extractive")],
    "R-11": [("tests.test_plana", "test_frontend_xss_safe")],
    "R-12": [("tests.test_plana", "test_health_readiness_fields"),
             ("tests.test_plana", "test_sources_endpoint_ct06"),
             ("tests.test_plana", "test_manifest_json_matches_corpus")],
    "R-15": [("tests.test_robustness", "test_degraded_state_visible_in_health"),
             ("tests.test_robustness", "test_validator_mode_reported")],
}


def test_every_requirement_has_tests():
    table = (ROOT / "docs" / "ACCEPTANCE.md").read_text(encoding="utf-8")
    ids = set(re.findall(r"\| (R-\d+) \|", table))
    assert ids >= set(REGISTRY), f"registry missing rows: {set(REGISTRY) - ids}"
    for req in ids - {"R-01", "R-02", "R-13", "R-14"}:
        assert req in REGISTRY, f"{req} has no mapped tests (add tests or mark OPEN)"


def test_mapped_tests_exist():
    import importlib
    for req, cases in REGISTRY.items():
        for mod, fn in cases:
            m = importlib.import_module(mod)
            assert callable(getattr(m, fn, None)), f"{req}: {mod}.{fn} missing"
