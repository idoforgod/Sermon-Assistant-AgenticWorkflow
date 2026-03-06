#!/usr/bin/env python3
"""
TDD Tests for _sermon_lib.py — Sermon Research Workflow Deterministic Library

Tests organized by function group:
  1. Schema Validation (GroundedClaim)
  2. Hallucination Firewall
  3. SRCS Scoring
  4. Cross-Validation Gate (structural)
  5. Checklist Management
  6. Session Initialization
  7. Error Handling
  8. Wave Boundary Detection
  9. Constants Integrity
  10. Agent Dependencies & Prompt Generation
  11. Agent Output Validation (extract + pipeline)
  12. Gate Completion Safety
  13. Translation Management (P1 routing, prompt, validation, pACS, glossary)
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure the script directory is in path
sys.path.insert(0, os.path.dirname(__file__))

from _sermon_lib import (
    AGENT_CLAIM_PREFIXES,
    AGENT_OUTPUT_FILES,
    CHECKLIST_SECTIONS,
    CLAIM_TYPE_SOURCE_REQUIREMENTS,
    CONFIDENCE_THRESHOLDS,
    FAILURE_HANDLERS,
    FAILURE_TYPES,
    INPUT_MODES,
    SRCS_WEIGHTS,
    VALID_CLAIM_TYPES,
    VALID_SOURCE_TYPES,
    WAVE_AGENTS,
    WAVE_GATE_MAP,
    calculate_agent_srcs,
    calculate_srcs_score,
    check_hallucination_firewall,
    check_pending_gate,
    confidence_check,
    create_output_structure,
    detect_input_mode,
    format_srcs_report,
    generate_checklist,
    generate_session_json,
    get_checklist_progress,
    get_current_wave,
    get_failure_handler,
    get_output_dir_name,
    has_blocking_hallucination,
    parse_agent_failure,
    update_checklist,
    validate_claim_id_prefix,
    validate_claims_batch,
    validate_gate_result,
    validate_gate_structure,
    validate_grounded_claim,
    validate_sermon_sot_schema,
    validate_srcs_output,
    handle_research_incomplete,
    handle_validation_failure,
    handle_srcs_below_threshold,
    AGENT_DEPENDENCIES,
    TRANSLATION_TARGETS,
    resolve_dependency_files,
    build_research_agent_prompt,
    extract_claims_from_output,
    validate_agent_output,
    record_gate_completion,
    get_translation_targets,
    build_translation_prompt,
    validate_translation_output,
    extract_translation_pacs,
    should_retranslate,
    collect_discovered_terms,
    merge_glossary_terms,
    update_translation_state,
    check_pending_translation,
    prepare_translation_batch,
    finalize_translation_batch,
    initialize_sermon_output,
    find_active_session,
    resolve_sermon_context,
    _build_sermon_path_map,
)


# ===================================================================
# 1. Constants Integrity Tests
# ===================================================================

class TestConstants(unittest.TestCase):
    """Verify constants match workflow.md definitions."""

    def test_claim_types_complete(self):
        expected = {"FACTUAL", "LINGUISTIC", "HISTORICAL",
                    "THEOLOGICAL", "INTERPRETIVE", "APPLICATIONAL"}
        self.assertEqual(VALID_CLAIM_TYPES, expected)

    def test_source_types_complete(self):
        expected = {"PRIMARY", "SECONDARY", "TERTIARY"}
        self.assertEqual(VALID_SOURCE_TYPES, expected)

    def test_all_claim_types_have_source_requirements(self):
        for ct in VALID_CLAIM_TYPES:
            self.assertIn(ct, CLAIM_TYPE_SOURCE_REQUIREMENTS,
                          f"Missing source requirement for {ct}")

    def test_all_claim_types_have_confidence_thresholds(self):
        for ct in VALID_CLAIM_TYPES:
            self.assertIn(ct, CONFIDENCE_THRESHOLDS,
                          f"Missing confidence threshold for {ct}")

    def test_all_claim_types_have_srcs_weights(self):
        for ct in VALID_CLAIM_TYPES:
            self.assertIn(ct, SRCS_WEIGHTS,
                          f"Missing SRCS weights for {ct}")

    def test_srcs_weights_sum_to_1(self):
        for ct, weights in SRCS_WEIGHTS.items():
            total = sum(weights.values())
            self.assertAlmostEqual(total, 1.0, places=2,
                                   msg=f"SRCS weights for {ct} sum to {total}")

    def test_wave_agents_cover_all_research_agents(self):
        all_wave_agents = set()
        for agents in WAVE_AGENTS.values():
            all_wave_agents.update(agents)
        self.assertEqual(all_wave_agents, set(AGENT_CLAIM_PREFIXES.keys()))

    def test_agent_output_files_cover_all_research_agents(self):
        for agent in AGENT_CLAIM_PREFIXES:
            self.assertIn(agent, AGENT_OUTPUT_FILES,
                          f"Missing output file for {agent}")

    def test_checklist_sections_sum_matches_workflow(self):
        total = sum(count for _, count in CHECKLIST_SECTIONS)
        # workflow.md table updated for translation steps: 155 total
        self.assertEqual(total, 155)

    def test_failure_types_complete(self):
        expected = {"LOOP_EXHAUSTED", "SOURCE_UNAVAILABLE", "INPUT_INVALID",
                    "CONFLICT_UNRESOLVABLE", "OUT_OF_SCOPE"}
        self.assertEqual(FAILURE_TYPES, expected)

    def test_all_failure_types_have_handlers(self):
        for ft in FAILURE_TYPES:
            self.assertIn(ft, FAILURE_HANDLERS,
                          f"Missing handler for {ft}")

    def test_input_modes_complete(self):
        expected = {"theme", "passage", "series"}
        self.assertEqual(INPUT_MODES, expected)


# ===================================================================
# 2. Schema Validation Tests
# ===================================================================

class TestGroundedClaimValidation(unittest.TestCase):

    def _valid_claim(self, **overrides):
        claim = {
            "id": "OTA-001",
            "text": "Test claim text",
            "claim_type": "FACTUAL",
            "sources": [
                {"type": "PRIMARY", "reference": "BDB, p.944", "verified": True}
            ],
            "confidence": 95,
            "uncertainty": None,
        }
        claim.update(overrides)
        return claim

    def test_valid_claim_no_errors(self):
        errors = validate_grounded_claim(self._valid_claim())
        self.assertEqual(errors, [])

    def test_missing_id(self):
        claim = self._valid_claim()
        del claim["id"]
        errors = validate_grounded_claim(claim)
        self.assertTrue(any("id" in e for e in errors))

    def test_empty_id(self):
        errors = validate_grounded_claim(self._valid_claim(id=""))
        self.assertTrue(any("id" in e for e in errors))

    def test_missing_text(self):
        claim = self._valid_claim()
        del claim["text"]
        errors = validate_grounded_claim(claim)
        self.assertTrue(any("text" in e for e in errors))

    def test_invalid_claim_type(self):
        errors = validate_grounded_claim(self._valid_claim(claim_type="INVALID"))
        self.assertTrue(any("claim_type" in e for e in errors))

    def test_missing_sources(self):
        claim = self._valid_claim()
        del claim["sources"]
        errors = validate_grounded_claim(claim)
        self.assertTrue(any("sources" in e for e in errors))

    def test_sources_not_list(self):
        errors = validate_grounded_claim(self._valid_claim(sources="not a list"))
        self.assertTrue(any("sources" in e for e in errors))

    def test_invalid_source_type(self):
        sources = [{"type": "INVALID", "reference": "test", "verified": True}]
        errors = validate_grounded_claim(self._valid_claim(sources=sources))
        self.assertTrue(any("type" in e for e in errors))

    def test_empty_source_reference(self):
        sources = [{"type": "PRIMARY", "reference": "", "verified": True}]
        errors = validate_grounded_claim(self._valid_claim(sources=sources))
        self.assertTrue(any("reference" in e for e in errors))

    def test_linguistic_requires_primary(self):
        sources = [{"type": "SECONDARY", "reference": "test", "verified": True}]
        errors = validate_grounded_claim(
            self._valid_claim(claim_type="LINGUISTIC", sources=sources)
        )
        self.assertTrue(any("PRIMARY" in e for e in errors))

    def test_applicational_no_source_required(self):
        errors = validate_grounded_claim(
            self._valid_claim(claim_type="APPLICATIONAL", sources=[], confidence=60)
        )
        self.assertEqual(errors, [])

    def test_confidence_out_of_range(self):
        errors = validate_grounded_claim(self._valid_claim(confidence=150))
        self.assertTrue(any("confidence" in e for e in errors))

    def test_confidence_negative(self):
        errors = validate_grounded_claim(self._valid_claim(confidence=-5))
        self.assertTrue(any("confidence" in e for e in errors))

    def test_uncertainty_string_valid(self):
        errors = validate_grounded_claim(
            self._valid_claim(uncertainty="Possibly later dating")
        )
        self.assertEqual(errors, [])

    def test_uncertainty_null_valid(self):
        errors = validate_grounded_claim(self._valid_claim(uncertainty=None))
        self.assertEqual(errors, [])

    def test_uncertainty_invalid_type(self):
        errors = validate_grounded_claim(self._valid_claim(uncertainty=123))
        self.assertTrue(any("uncertainty" in e for e in errors))


class TestClaimIdPrefix(unittest.TestCase):

    def test_valid_prefix(self):
        result = validate_claim_id_prefix("OTA-001", "original-text-analyst")
        self.assertIsNone(result)

    def test_invalid_prefix(self):
        result = validate_claim_id_prefix("XX-001", "original-text-analyst")
        self.assertIsNotNone(result)
        self.assertIn("OTA", result)

    def test_unknown_agent_skips(self):
        result = validate_claim_id_prefix("XX-001", "unknown-agent")
        self.assertIsNone(result)


class TestClaimsBatch(unittest.TestCase):

    def _valid_claim(self, id_suffix="001"):
        return {
            "id": f"OTA-{id_suffix}",
            "text": "Test",
            "claim_type": "FACTUAL",
            "sources": [{"type": "PRIMARY", "reference": "test", "verified": True}],
            "confidence": 95,
            "uncertainty": None,
        }

    def test_valid_batch(self):
        result = validate_claims_batch(
            [self._valid_claim("001"), self._valid_claim("002")],
            agent_name="original-text-analyst",
        )
        self.assertTrue(result["valid"])
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["errors"]), 0)

    def test_duplicate_ids_detected(self):
        result = validate_claims_batch(
            [self._valid_claim("001"), self._valid_claim("001")]
        )
        self.assertFalse(result["valid"])
        self.assertIn("OTA-001", result["duplicate_ids"])

    def test_non_dict_claim(self):
        result = validate_claims_batch(["not a dict"])
        self.assertFalse(result["valid"])


# ===================================================================
# 3. Hallucination Firewall Tests
# ===================================================================

class TestHallucinationFirewall(unittest.TestCase):

    def test_block_all_scholars_agree(self):
        findings = check_hallucination_firewall("All scholars agree on this point.")
        block_findings = [f for f in findings if f["level"] == "BLOCK"]
        self.assertGreater(len(block_findings), 0)

    def test_block_100_percent(self):
        findings = check_hallucination_firewall("This is 100% certain.")
        block_findings = [f for f in findings if f["level"] == "BLOCK"]
        self.assertGreater(len(block_findings), 0)

    def test_block_without_exception(self):
        findings = check_hallucination_firewall("Without exception, this holds.")
        block_findings = [f for f in findings if f["level"] == "BLOCK"]
        self.assertGreater(len(block_findings), 0)

    def test_require_source_exact_number(self):
        findings = check_hallucination_firewall("There are exactly 12 occurrences.")
        req_findings = [f for f in findings if f["level"] == "REQUIRE_SOURCE"]
        self.assertGreater(len(req_findings), 0)

    def test_require_source_bc_date(self):
        findings = check_hallucination_firewall("Written in BC 587.")
        req_findings = [f for f in findings if f["level"] == "REQUIRE_SOURCE"]
        self.assertGreater(len(req_findings), 0)

    def test_soften_certainly(self):
        findings = check_hallucination_firewall("This certainly means...")
        soften = [f for f in findings if f["level"] == "SOFTEN"]
        self.assertGreater(len(soften), 0)

    def test_verify_dr_claims(self):
        findings = check_hallucination_firewall("Dr. Wright argues that...")
        verify = [f for f in findings if f["level"] == "VERIFY"]
        self.assertGreater(len(verify), 0)

    def test_verify_traditionally(self):
        findings = check_hallucination_firewall("Traditionally, this passage...")
        verify = [f for f in findings if f["level"] == "VERIFY"]
        self.assertGreater(len(verify), 0)

    def test_clean_text_no_findings(self):
        findings = check_hallucination_firewall(
            "The Hebrew word means 'shepherd' according to BDB p.944."
        )
        self.assertEqual(len(findings), 0)

    def test_has_blocking_true(self):
        self.assertTrue(has_blocking_hallucination("All scholars agree."))

    def test_has_blocking_false(self):
        self.assertFalse(has_blocking_hallucination("Some scholars suggest."))

    def test_findings_sorted_by_position(self):
        text = "Certainly, all scholars agree this is obviously true."
        findings = check_hallucination_firewall(text)
        positions = [f["position"] for f in findings]
        self.assertEqual(positions, sorted(positions))


# ===================================================================
# 4. SRCS Scoring Tests
# ===================================================================

class TestSRCSScoring(unittest.TestCase):

    def test_perfect_factual_score(self):
        result = calculate_srcs_score("FACTUAL", 100, 100, 100, 100)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["weighted_score"], 100.0)

    def test_zero_scores(self):
        result = calculate_srcs_score("FACTUAL", 0, 0, 0, 0)
        self.assertAlmostEqual(result["weighted_score"], 0.0)

    def test_factual_weights(self):
        # CS=0.3, GS=0.4, US=0.1, VS=0.2
        result = calculate_srcs_score("FACTUAL", 80, 90, 70, 85)
        expected = 80*0.3 + 90*0.4 + 70*0.1 + 85*0.2
        self.assertAlmostEqual(result["weighted_score"], round(expected, 2))

    def test_invalid_claim_type(self):
        result = calculate_srcs_score("INVALID", 80, 80, 80, 80)
        self.assertIsNone(result)

    def test_agent_srcs_empty(self):
        result = calculate_agent_srcs([])
        self.assertEqual(result["total_claims"], 0)
        self.assertEqual(result["average_score"], 0.0)

    def test_agent_srcs_with_below_threshold(self):
        scores = [
            calculate_srcs_score("FACTUAL", 60, 60, 60, 60),  # Below 95
            calculate_srcs_score("FACTUAL", 100, 100, 100, 100),
        ]
        result = calculate_agent_srcs(scores)
        self.assertEqual(result["total_claims"], 2)
        self.assertGreater(len(result["below_threshold"]), 0)


class TestSRCSOutputValidation(unittest.TestCase):

    def test_valid_output(self):
        result = {
            "average_score": 85.0,
            "min_score": 70.0,
            "max_score": 100.0,
            "total_claims": 10,
            "below_threshold": [],
        }
        errors = validate_srcs_output(result)
        self.assertEqual(errors, [])

    def test_missing_keys(self):
        errors = validate_srcs_output({})
        self.assertGreater(len(errors), 0)

    def test_invalid_total_claims(self):
        result = {
            "average_score": 85.0, "min_score": 70.0,
            "max_score": 100.0, "total_claims": -1,
            "below_threshold": [],
        }
        errors = validate_srcs_output(result)
        self.assertTrue(any("total_claims" in e for e in errors))


# ===================================================================
# 5. Cross-Validation Gate Tests
# ===================================================================

class TestGateStructure(unittest.TestCase):

    def test_unknown_gate(self):
        result = validate_gate_structure("gate-99", "/tmp/test")
        self.assertFalse(result["passed"])
        self.assertIn("error", result)

    def test_missing_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validate_gate_structure("gate-1", tmpdir)
            self.assertFalse(result["passed"])
            self.assertGreater(len(result["missing_files"]), 0)

    def test_all_files_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            research_dir = os.path.join(tmpdir, "research-package")
            os.makedirs(research_dir)
            for agent in WAVE_AGENTS["wave-1"]:
                filepath = os.path.join(research_dir, AGENT_OUTPUT_FILES[agent])
                with open(filepath, "w") as f:
                    f.write("claims:\n" + "x" * 200)
            result = validate_gate_structure("gate-1", tmpdir)
            self.assertTrue(result["passed"])

    def test_empty_file_detected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            research_dir = os.path.join(tmpdir, "research-package")
            os.makedirs(research_dir)
            for agent in WAVE_AGENTS["wave-1"]:
                filepath = os.path.join(research_dir, AGENT_OUTPUT_FILES[agent])
                with open(filepath, "w") as f:
                    f.write("tiny")  # < 100 bytes
            result = validate_gate_structure("gate-1", tmpdir)
            self.assertFalse(result["passed"])
            self.assertGreater(len(result["empty_files"]), 0)


class TestGateResult(unittest.TestCase):

    def test_both_passed(self):
        result = validate_gate_result("gate-1", True, True)
        self.assertTrue(result["passed"])

    def test_structural_failed(self):
        result = validate_gate_result("gate-1", False, True)
        self.assertFalse(result["passed"])

    def test_semantic_failed(self):
        result = validate_gate_result("gate-1", True, False, ["Contradiction found"])
        self.assertFalse(result["passed"])
        self.assertEqual(len(result["findings"]), 1)

    def test_has_timestamp(self):
        result = validate_gate_result("gate-1", True, True)
        self.assertIn("timestamp", result)


# ===================================================================
# 6. Checklist Tests
# ===================================================================

class TestChecklist(unittest.TestCase):

    def test_generate_checklist_not_empty(self):
        content = generate_checklist()
        self.assertIn("Checklist", content)
        self.assertIn("Step 1:", content)
        self.assertIn("- [ ]", content)

    def test_generate_checklist_has_all_sections(self):
        content = generate_checklist()
        for section_name, _ in CHECKLIST_SECTIONS:
            self.assertIn(section_name, content,
                          f"Missing section: {section_name}")

    def test_update_checklist(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md",
                                          delete=False) as f:
            f.write(generate_checklist())
            path = f.name
        try:
            result = update_checklist(path, 1, completed=True)
            self.assertTrue(result)
            with open(path) as f:
                content = f.read()
            self.assertIn("- [x] Step 1:", content)
            self.assertIn("Completed: 1/", content)
        finally:
            os.unlink(path)

    def test_update_nonexistent_step(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md",
                                          delete=False) as f:
            f.write(generate_checklist())
            path = f.name
        try:
            result = update_checklist(path, 9999, completed=True)
            self.assertFalse(result)
        finally:
            os.unlink(path)

    def test_get_progress_empty(self):
        result = get_checklist_progress("/nonexistent/file.md")
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["completed"], 0)

    def test_get_progress_with_completions(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md",
                                          delete=False) as f:
            f.write(generate_checklist())
            path = f.name
        try:
            update_checklist(path, 1, completed=True)
            update_checklist(path, 2, completed=True)
            progress = get_checklist_progress(path)
            self.assertEqual(progress["completed"], 2)
            self.assertEqual(progress["last_completed_step"], 2)
            self.assertEqual(progress["next_step"], 3)
            self.assertGreater(progress["percentage"], 0)
        finally:
            os.unlink(path)


# ===================================================================
# 7. Session Initialization Tests
# ===================================================================

class TestSessionInit(unittest.TestCase):

    def test_generate_session_json_theme(self):
        result = generate_session_json("theme", "Trusting God in suffering")
        self.assertEqual(result["mode"], "theme")
        self.assertEqual(result["input"], "Trusting God in suffering")
        self.assertEqual(result["status"], "initialized")
        self.assertIn("context_snapshots", result)
        # v2.1: translation_state must be present
        self.assertIn("translation_state", result)
        ts = result["translation_state"]
        self.assertEqual(ts["completed_phases"], [])
        self.assertEqual(ts["glossary_terms_added"], 0)
        self.assertIsNone(ts["glossary_updated_at"])
        self.assertEqual(ts["failed_translations"], [])

    def test_generate_session_json_passage(self):
        result = generate_session_json("passage", "Psalm 23:1-6")
        self.assertEqual(result["mode"], "passage")

    def test_invalid_mode_defaults_to_theme(self):
        result = generate_session_json("invalid", "test")
        self.assertEqual(result["mode"], "theme")

    def test_get_output_dir_name(self):
        name = get_output_dir_name("Trust in God")
        self.assertTrue(name.startswith("sermon-output/"))
        self.assertIn("Trust-in-God", name)

    def test_get_output_dir_name_colon_to_hyphen(self):
        name = get_output_dir_name("Romans 8:1-10")
        self.assertIn("Romans-8-1-10", name)
        self.assertNotIn("81-10", name)  # colon must not be silently deleted

    def test_get_output_dir_name_korean_passage(self):
        name = get_output_dir_name("로마서 8:1-10")
        self.assertIn("로마서-8-1-10", name)

    def test_create_output_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = os.path.join(tmpdir, "test-output")
            dirs = create_output_structure(base)
            self.assertTrue(os.path.isdir(dirs["root"]))
            self.assertTrue(os.path.isdir(dirs["research"]))
            self.assertTrue(os.path.isdir(dirs["temp"]))


class TestInputModeDetection(unittest.TestCase):

    def test_passage_with_reference(self):
        self.assertEqual(detect_input_mode("시편 23:1-6"), "passage")

    def test_passage_english(self):
        self.assertEqual(detect_input_mode("Psalm 23:1-6"), "passage")

    def test_series_korean(self):
        self.assertEqual(detect_input_mode("요한복음 강해 시리즈 3주차"), "series")

    def test_series_english(self):
        self.assertEqual(detect_input_mode("Week 3 of John series"), "series")

    def test_theme_default(self):
        self.assertEqual(
            detect_input_mode("고난 중에도 하나님을 신뢰하는 것"),
            "theme",
        )

    def test_theme_english(self):
        self.assertEqual(
            detect_input_mode("Trusting God in times of suffering"),
            "theme",
        )


# ===================================================================
# 8. Error Handling Tests
# ===================================================================

class TestErrorHandling(unittest.TestCase):

    def test_parse_loop_exhausted(self):
        output = "After 3 attempts... [FAILURE:LOOP_EXHAUSTED] partial results below."
        self.assertEqual(parse_agent_failure(output), "LOOP_EXHAUSTED")

    def test_parse_source_unavailable(self):
        output = "Cannot access BDB. FAILURE:SOURCE_UNAVAILABLE"
        self.assertEqual(parse_agent_failure(output), "SOURCE_UNAVAILABLE")

    def test_parse_no_failure(self):
        output = "Analysis complete. All claims verified."
        self.assertIsNone(parse_agent_failure(output))

    def test_all_failure_types_parseable(self):
        for ft in FAILURE_TYPES:
            output = f"[FAILURE:{ft}] Something went wrong."
            self.assertEqual(parse_agent_failure(output), ft,
                             f"Failed to parse {ft}")

    def test_get_handler_known(self):
        handler = get_failure_handler("LOOP_EXHAUSTED")
        self.assertIsNotNone(handler)
        self.assertEqual(handler["action"], "return_partial")

    def test_get_handler_unknown(self):
        handler = get_failure_handler("UNKNOWN_TYPE")
        self.assertIsNone(handler)


# ===================================================================
# 9. Wave Boundary Tests
# ===================================================================

class TestWaveBoundary(unittest.TestCase):

    def test_step_1_is_phase_0(self):
        wave = get_current_wave(1)
        self.assertIsNotNone(wave)
        self.assertNotIn("wave", wave.lower() if wave else "")

    def test_wave_1_detection(self):
        # Wave 1 starts after Phase 0 (6) + Phase 0-A (8) + HITL-1 (3) = step 18
        wave = get_current_wave(18)
        self.assertEqual(wave, "wave-1")

    def test_check_pending_gate_none(self):
        result = check_pending_gate(1, [])
        self.assertIsNone(result)

    def test_check_pending_gate_detected(self):
        # Wave 1 ends at step 6+8+3+16 = 33, gate-1 fires after step 33
        # Step 34 is past wave-1 end, so gate-1 should be pending
        result = check_pending_gate(34, [])
        self.assertEqual(result, "gate-1")

    def test_check_pending_gate_completed(self):
        result = check_pending_gate(34, ["gate-1"])
        # gate-1 already completed, should not return gate-1
        self.assertNotEqual(result, "gate-1",
                            "gate-1 should not be pending after completion")


# ===================================================================
# 10. Utility Tests
# ===================================================================

class TestUtilities(unittest.TestCase):

    def test_confidence_check_passes(self):
        result = confidence_check("FACTUAL", 95)
        self.assertTrue(result["meets_threshold"])

    def test_confidence_check_fails(self):
        result = confidence_check("FACTUAL", 80)
        self.assertFalse(result["meets_threshold"])
        self.assertEqual(result["threshold"], 95)

    def test_format_srcs_report_markdown(self):
        agent_results = {
            "original-text-analyst": {
                "average_score": 90.0,
                "min_score": 85.0,
                "max_score": 95.0,
                "total_claims": 5,
                "below_threshold": [],
            },
        }
        report = format_srcs_report(agent_results)
        self.assertIn("SRCS Evaluation Summary", report)
        self.assertIn("original-text-analyst", report)
        self.assertIn("90.0", report)

    def test_format_srcs_report_flags_below_threshold(self):
        agent_results = {
            "test-agent": {
                "average_score": 50.0,
                "min_score": 40.0,
                "max_score": 60.0,
                "total_claims": 1,
                "below_threshold": [
                    {"claim_type": "FACTUAL", "score": 50.0, "threshold": 95},
                ],
            },
        }
        report = format_srcs_report(agent_results)
        self.assertIn("Below Threshold", report)


# ===================================================================
# 11. Sermon SOT Schema Validation Tests
# ===================================================================

class TestSermonSotSchema(unittest.TestCase):

    def test_valid_sermon_state(self):
        state = {
            "mode": "passage",
            "passage": "Psalm 23:1-6",
            "output_dir": "sermon-output/test",
            "completed_gates": ["gate-1"],
            "srcs_threshold": 70,
        }
        warnings = validate_sermon_sot_schema(state)
        self.assertEqual(warnings, [])

    def test_invalid_mode(self):
        state = {"mode": "invalid"}
        warnings = validate_sermon_sot_schema(state)
        self.assertTrue(any("mode" in w for w in warnings))

    def test_invalid_gate(self):
        state = {"completed_gates": ["gate-1", "gate-99"]}
        warnings = validate_sermon_sot_schema(state)
        self.assertTrue(any("gate-99" in w for w in warnings))

    def test_invalid_threshold(self):
        state = {"srcs_threshold": 150}
        warnings = validate_sermon_sot_schema(state)
        self.assertTrue(any("srcs_threshold" in w for w in warnings))

    def test_empty_state(self):
        warnings = validate_sermon_sot_schema({})
        self.assertEqual(warnings, [])

    def test_none_state(self):
        warnings = validate_sermon_sot_schema(None)
        self.assertEqual(warnings, [])


# ===================================================================
# 12. Workflow-Level Error Handler Tests
# ===================================================================

class TestWorkflowLevelHandlers(unittest.TestCase):

    def test_research_incomplete_detects_missing(self):
        result = handle_research_incomplete(
            completed_agents=["original-text-analyst", "manuscript-comparator"],
            expected_agents=WAVE_AGENTS["wave-1"],
        )
        self.assertEqual(result["action"], "partial_proceed")
        self.assertTrue(result["notify"])
        self.assertEqual(len(result["missing_agents"]), 2)
        self.assertIn("biblical-geography-expert", result["missing_agents"])

    def test_research_incomplete_all_complete(self):
        result = handle_research_incomplete(
            completed_agents=WAVE_AGENTS["wave-1"],
            expected_agents=WAVE_AGENTS["wave-1"],
        )
        self.assertEqual(result["missing_agents"], [])

    def test_validation_failure_structural(self):
        result = handle_validation_failure(
            gate_name="gate-1",
            structural_passed=False,
            semantic_passed=True,
        )
        self.assertEqual(result["action"], "request_human_review")
        self.assertIn("structural", result["failure_reasons"][0])

    def test_validation_failure_semantic(self):
        result = handle_validation_failure(
            gate_name="gate-2",
            structural_passed=True,
            semantic_passed=False,
            findings=["Contradiction between TA-001 and LA-003"],
        )
        self.assertEqual(result["action"], "request_human_review")
        self.assertEqual(len(result["findings"]), 1)

    def test_srcs_below_threshold_flags(self):
        agent_results = {
            "agent-a": {"average_score": 50.0, "below_threshold": [{"x": 1}]},
            "agent-b": {"average_score": 80.0, "below_threshold": []},
        }
        result = handle_srcs_below_threshold(agent_results, threshold=70)
        self.assertEqual(result["action"], "flag_for_review")
        self.assertEqual(result["flagged_count"], 1)
        self.assertTrue(result["requires_review"])

    def test_srcs_all_above_threshold(self):
        agent_results = {
            "agent-a": {"average_score": 85.0, "below_threshold": []},
        }
        result = handle_srcs_below_threshold(agent_results, threshold=70)
        self.assertEqual(result["flagged_count"], 0)
        self.assertFalse(result["requires_review"])


# ===================================================================
# 13. Korean Hallucination Firewall Tests
# ===================================================================

class TestKoreanHallucinationFirewall(unittest.TestCase):

    def test_korean_block_all_scholars(self):
        text = "모든 학자가 동의하는 바와 같이"
        findings = check_hallucination_firewall(text)
        block = [f for f in findings if f["level"] == "BLOCK"]
        self.assertGreater(len(block), 0)

    def test_korean_block_no_exception(self):
        text = "예외 없이 모든 경우에"
        findings = check_hallucination_firewall(text)
        block = [f for f in findings if f["level"] == "BLOCK"]
        self.assertGreater(len(block), 0)

    def test_korean_block_universally(self):
        text = "보편적으로 인정되는 사실"
        findings = check_hallucination_firewall(text)
        block = [f for f in findings if f["level"] == "BLOCK"]
        self.assertGreater(len(block), 0)

    def test_korean_block_no_dissent(self):
        text = "반론의 여지가 없는 결론"
        findings = check_hallucination_firewall(text)
        block = [f for f in findings if f["level"] == "BLOCK"]
        self.assertGreater(len(block), 0)

    def test_korean_safe_text(self):
        text = "일부 학자들은 이 해석에 동의하지만, 다른 견해도 존재합니다."
        findings = check_hallucination_firewall(text)
        block = [f for f in findings if f["level"] == "BLOCK"]
        self.assertEqual(len(block), 0)


# ===================================================================
# 10. Agent Dependencies & Prompt Generation Tests
# ===================================================================

class TestAgentDependencies(unittest.TestCase):
    """Verify AGENT_DEPENDENCIES matches workflow.md:765-808."""

    def test_all_research_agents_have_entry(self):
        for agent in AGENT_OUTPUT_FILES:
            self.assertIn(agent, AGENT_DEPENDENCIES)

    def test_wave1_agents_independent(self):
        wave1 = WAVE_AGENTS["wave-1"]
        for agent in wave1:
            self.assertEqual(AGENT_DEPENDENCIES[agent], [])

    def test_wave2_depend_on_wave1(self):
        wave1 = set(WAVE_AGENTS["wave-1"])
        for agent in WAVE_AGENTS["wave-2"]:
            deps = AGENT_DEPENDENCIES[agent]
            self.assertTrue(len(deps) > 0, f"{agent} should have deps")
            for dep in deps:
                self.assertIn(dep, wave1, f"{agent} dep {dep} not in wave-1")

    def test_wave3_depend_on_wave2_or_wave1(self):
        upstream = set(WAVE_AGENTS["wave-1"]) | set(WAVE_AGENTS["wave-2"])
        for agent in WAVE_AGENTS["wave-3"]:
            deps = AGENT_DEPENDENCIES[agent]
            self.assertTrue(len(deps) > 0, f"{agent} should have deps")
            for dep in deps:
                self.assertIn(dep, upstream)

    def test_wave4_depend_on_wave3(self):
        wave3 = set(WAVE_AGENTS["wave-3"])
        for agent in WAVE_AGENTS["wave-4"]:
            deps = AGENT_DEPENDENCIES[agent]
            self.assertTrue(len(deps) > 0, f"{agent} should have deps")
            for dep in deps:
                self.assertIn(dep, wave3)

    def test_no_circular_dependencies(self):
        """Verify no agent depends on itself or creates a cycle."""
        for agent, deps in AGENT_DEPENDENCIES.items():
            self.assertNotIn(agent, deps, f"{agent} depends on itself")


class TestResolveDependencyFiles(unittest.TestCase):

    def test_wave1_returns_empty(self):
        result = resolve_dependency_files("original-text-analyst", "/out")
        self.assertEqual(result, [])

    def test_wave2_returns_correct_paths(self):
        result = resolve_dependency_files("structure-analyst", "/out")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["agent"], "original-text-analyst")
        self.assertIn("01-original-text-analysis.md", result[0]["path"])

    def test_unknown_agent_returns_empty(self):
        result = resolve_dependency_files("nonexistent-agent", "/out")
        self.assertEqual(result, [])


class TestBuildResearchAgentPrompt(unittest.TestCase):

    def test_wave1_agent_no_deps_section(self):
        prompt = build_research_agent_prompt(
            "original-text-analyst", "Psalm 23:1-6", "/out", "Standard")
        self.assertIsNotNone(prompt)
        self.assertIn("Psalm 23:1-6", prompt)
        self.assertIn("01-original-text-analysis.md", prompt)
        self.assertIn("gra-compliance.md", prompt)
        self.assertNotIn("Dependency Files", prompt)

    def test_wave2_agent_has_deps_section(self):
        prompt = build_research_agent_prompt(
            "structure-analyst", "Genesis 1:1-3", "/out", "Advanced")
        self.assertIsNotNone(prompt)
        self.assertIn("Dependency Files", prompt)
        self.assertIn("original-text-analyst", prompt)
        self.assertIn("01-original-text-analysis.md", prompt)
        self.assertIn("Advanced", prompt)

    def test_wave4_agent_has_literary_dep(self):
        prompt = build_research_agent_prompt(
            "rhetorical-analyst", "John 3:16", "/out")
        self.assertIn("literary-analyst", prompt)
        self.assertIn("06-literary-analysis.md", prompt)

    def test_non_research_agent_returns_none(self):
        prompt = build_research_agent_prompt(
            "sermon-writer", "Psalm 23", "/out")
        self.assertIsNone(prompt)

    def test_all_research_agents_produce_prompt(self):
        for agent in AGENT_OUTPUT_FILES:
            prompt = build_research_agent_prompt(
                agent, "Test passage", "/out")
            self.assertIsNotNone(prompt, f"{agent} should produce a prompt")
            self.assertIn("Runtime Parameters", prompt)
            self.assertIn("gra-compliance.md", prompt)


# ===================================================================
# 11. Agent Output Validation Tests
# ===================================================================

class TestExtractClaimsFromOutput(unittest.TestCase):

    def _write_temp(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".md")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_extract_fenced_yaml(self):
        content = """# Analysis

Some text here.

```yaml
claims:
  - id: "OTA-001"
    text: "Test claim"
    claim_type: FACTUAL
    sources:
      - type: PRIMARY
        reference: "BDB p.100"
        verified: true
    confidence: 95
    uncertainty: null
```

More text.
"""
        path = self._write_temp(content)
        try:
            result = extract_claims_from_output(path)
            self.assertTrue(result["success"])
            self.assertEqual(len(result["claims"]), 1)
            self.assertEqual(result["claims"][0]["id"], "OTA-001")
            self.assertIsNone(result["error"])
        finally:
            os.unlink(path)

    def test_extract_multiple_yaml_blocks(self):
        content = """# Analysis

```yaml
claims:
  - id: "OTA-001"
    text: "First"
    claim_type: FACTUAL
    sources: []
    confidence: 90
    uncertainty: null
```

More analysis.

```yaml
claims:
  - id: "OTA-002"
    text: "Second"
    claim_type: LINGUISTIC
    sources: []
    confidence: 85
    uncertainty: null
```
"""
        path = self._write_temp(content)
        try:
            result = extract_claims_from_output(path)
            self.assertTrue(result["success"])
            self.assertEqual(len(result["claims"]), 2)
        finally:
            os.unlink(path)

    def test_extract_unfenced_claims(self):
        content = """# Analysis

claims:
  - id: "OTA-001"
    text: "Unfenced claim"
    claim_type: HISTORICAL
    sources: []
    confidence: 80
    uncertainty: null
"""
        path = self._write_temp(content)
        try:
            result = extract_claims_from_output(path)
            self.assertTrue(result["success"])
            self.assertEqual(len(result["claims"]), 1)
        finally:
            os.unlink(path)

    def test_no_claims_block(self):
        content = "# Analysis\n\nJust some text without claims."
        path = self._write_temp(content)
        try:
            result = extract_claims_from_output(path)
            self.assertFalse(result["success"])
            self.assertIn("No YAML claims block", result["error"])
        finally:
            os.unlink(path)

    def test_nonexistent_file(self):
        result = extract_claims_from_output("/nonexistent/path.md")
        self.assertFalse(result["success"])
        self.assertIn("Cannot read file", result["error"])

    def test_yaml_block_without_claims_key(self):
        content = """```yaml
metadata:
  author: "test"
```"""
        path = self._write_temp(content)
        try:
            result = extract_claims_from_output(path)
            self.assertFalse(result["success"])
            self.assertIn("no valid 'claims' key", result["error"])
        finally:
            os.unlink(path)


class TestValidateAgentOutput(unittest.TestCase):

    def _write_temp(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".md")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_valid_output(self):
        content = """# Original Text Analysis

Detailed analysis of the passage.

```yaml
claims:
  - id: "OTA-001"
    text: "Test claim about Hebrew text"
    claim_type: LINGUISTIC
    sources:
      - type: PRIMARY
        reference: "BDB p.944"
        verified: true
    confidence: 95
    uncertainty: null
```

## Methodology Notes
Used CoT analysis.
"""
        path = self._write_temp(content)
        try:
            result = validate_agent_output(path, "original-text-analyst")
            self.assertTrue(result["valid"], f"Errors: {result['errors']}")
            self.assertTrue(result["l0"]["exists"])
            self.assertTrue(result["l0"]["size_ok"])
            self.assertEqual(result["claims"]["extracted"], 1)
            self.assertEqual(result["firewall"]["block_count"], 0)
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        result = validate_agent_output("/nonexistent.md", "original-text-analyst")
        self.assertFalse(result["valid"])
        self.assertFalse(result["l0"]["exists"])

    def test_file_too_small(self):
        path = self._write_temp("tiny")
        try:
            result = validate_agent_output(path, "original-text-analyst")
            self.assertFalse(result["valid"])
            self.assertFalse(result["l0"]["size_ok"])
        finally:
            os.unlink(path)

    def test_hallucination_detected(self):
        content = """# Analysis

All scholars agree that this is the correct interpretation.

```yaml
claims:
  - id: "OTA-001"
    text: "A claim"
    claim_type: FACTUAL
    sources:
      - type: PRIMARY
        reference: "Source"
        verified: true
    confidence: 95
    uncertainty: null
```
"""
        path = self._write_temp(content)
        try:
            result = validate_agent_output(path, "original-text-analyst")
            self.assertFalse(result["valid"])
            self.assertGreater(result["firewall"]["block_count"], 0)
        finally:
            os.unlink(path)

    def test_non_gra_agent_skips_claims(self):
        """Non-GRA agents skip claim extraction but still run L0 + firewall."""
        content = "# Sermon Draft\n\n" + "x" * 200
        path = self._write_temp(content)
        try:
            result = validate_agent_output(path, "sermon-writer")
            self.assertTrue(result["valid"])
            self.assertEqual(result["claims"]["extracted"], 0)
        finally:
            os.unlink(path)

    def test_invalid_claims_flagged(self):
        content = """# Analysis

```yaml
claims:
  - id: "OTA-001"
    text: ""
    claim_type: INVALID_TYPE
    sources: []
    confidence: 150
    uncertainty: null
```
""" + "x" * 50
        path = self._write_temp(content)
        try:
            result = validate_agent_output(path, "original-text-analyst")
            self.assertFalse(result["valid"])
            self.assertGreater(len(result["claims"]["errors"]), 0)
        finally:
            os.unlink(path)


# ===================================================================
# 12. Gate Completion Safety Tests
# ===================================================================

class TestRecordGateCompletion(unittest.TestCase):

    def test_valid_gate1_completion(self):
        state = {"completed_gates": []}
        result = record_gate_completion(state, "gate-1")
        self.assertTrue(result["success"])
        self.assertEqual(result["sermon_state"]["completed_gates"], ["gate-1"])
        self.assertIsNone(result["error"])

    def test_sequential_gate_completion(self):
        state = {"completed_gates": ["gate-1"]}
        result = record_gate_completion(state, "gate-2")
        self.assertTrue(result["success"])
        self.assertEqual(
            result["sermon_state"]["completed_gates"], ["gate-1", "gate-2"])

    def test_reject_invalid_gate_name(self):
        state = {"completed_gates": []}
        result = record_gate_completion(state, "gate-4")
        self.assertFalse(result["success"])
        self.assertIn("Invalid gate name", result["error"])

    def test_reject_duplicate_gate(self):
        state = {"completed_gates": ["gate-1"]}
        result = record_gate_completion(state, "gate-1")
        self.assertFalse(result["success"])
        self.assertIn("already recorded", result["error"])

    def test_reject_out_of_order(self):
        state = {"completed_gates": []}
        result = record_gate_completion(state, "gate-2")
        self.assertFalse(result["success"])
        self.assertIn("gate-1", result["error"])

    def test_reject_gate3_without_gate2(self):
        state = {"completed_gates": ["gate-1"]}
        result = record_gate_completion(state, "gate-3")
        self.assertFalse(result["success"])
        self.assertIn("gate-2", result["error"])

    def test_full_sequence(self):
        state = {"completed_gates": []}
        for gate in ["gate-1", "gate-2", "gate-3"]:
            result = record_gate_completion(state, gate)
            self.assertTrue(result["success"], f"Failed at {gate}")
            state = result["sermon_state"]
        self.assertEqual(
            state["completed_gates"], ["gate-1", "gate-2", "gate-3"])

    def test_does_not_mutate_original(self):
        state = {"completed_gates": []}
        record_gate_completion(state, "gate-1")
        self.assertEqual(state["completed_gates"], [])

    def test_handles_missing_completed_gates(self):
        state = {}
        result = record_gate_completion(state, "gate-1")
        self.assertTrue(result["success"])


# ===================================================================
# 13. Translation Management Tests (P1 Pipeline)
# ===================================================================

class TestTranslationTargets(unittest.TestCase):
    """Verify TRANSLATION_TARGETS constant integrity."""

    def test_all_research_files_covered(self):
        """Every AGENT_OUTPUT_FILES value must appear in some wave target."""
        wave_keys = ["wave-1", "wave-2", "wave-3", "wave-4"]
        all_wave_files = []
        for k in wave_keys:
            all_wave_files.extend(TRANSLATION_TARGETS[k])
        for agent, filename in AGENT_OUTPUT_FILES.items():
            self.assertIn(filename, all_wave_files,
                          f"Research file {filename} not in any wave target")

    def test_wave_file_counts_match_agents(self):
        self.assertEqual(len(TRANSLATION_TARGETS["wave-1"]), 4)
        self.assertEqual(len(TRANSLATION_TARGETS["wave-2"]), 3)
        self.assertEqual(len(TRANSLATION_TARGETS["wave-3"]), 3)
        # wave-4: rhetorical + confidence-report + research-synthesis
        self.assertEqual(len(TRANSLATION_TARGETS["wave-4"]), 3)

    def test_phase_2_3_targets_exist(self):
        self.assertEqual(TRANSLATION_TARGETS["phase-2-message"],
                         ["core-message.md"])
        self.assertEqual(TRANSLATION_TARGETS["phase-2-outline"],
                         ["sermon-outline.md"])
        self.assertEqual(TRANSLATION_TARGETS["phase-3-draft"],
                         ["sermon-draft.md"])
        self.assertEqual(TRANSLATION_TARGETS["phase-3-review"],
                         ["review-report.md"])
        self.assertEqual(TRANSLATION_TARGETS["phase-3-final"],
                         ["sermon-final.md"])


class TestGetTranslationTargets(unittest.TestCase):

    def test_wave1_returns_4_pairs(self):
        result = get_translation_targets("wave-1", "/out")
        self.assertEqual(len(result), 4)
        for item in result:
            self.assertIn("source", item)
            self.assertIn("target", item)
            self.assertTrue(item["target"].endswith(".ko.md"))
            self.assertIn("research-package", item["source"])

    def test_phase_2_message_returns_1_pair(self):
        result = get_translation_targets("phase-2-message", "/out")
        self.assertEqual(len(result), 1)
        self.assertIn("core-message.md", result[0]["source"])
        self.assertIn("core-message.ko.md", result[0]["target"])
        # Non-research files should NOT be in research-package/
        self.assertNotIn("research-package", result[0]["source"])

    def test_unknown_phase_returns_empty(self):
        result = get_translation_targets("nonexistent", "/out")
        self.assertEqual(result, [])

    def test_ko_md_naming_convention(self):
        """All targets must follow .ko.md naming."""
        for phase, files in TRANSLATION_TARGETS.items():
            result = get_translation_targets(phase, "/out")
            for item in result:
                base = os.path.basename(item["target"])
                self.assertTrue(base.endswith(".ko.md"),
                                f"{base} doesn't end with .ko.md")


class TestBuildTranslationPrompt(unittest.TestCase):

    def test_basic_prompt_structure(self):
        prompt = build_translation_prompt(
            "/out/research-package/01-original-text-analysis.md",
            "/glossary.yaml",
            "/out",
        )
        self.assertIn("Runtime Parameters", prompt)
        self.assertIn("01-original-text-analysis.md", prompt)
        self.assertIn("01-original-text-analysis.ko.md", prompt)
        self.assertIn("/glossary.yaml", prompt)
        self.assertIn("pacs-logs", prompt)

    def test_prompt_contains_instructions(self):
        prompt = build_translation_prompt("/src.md", "/g.yaml", "/out")
        self.assertIn("Instructions", prompt)
        self.assertIn("glossary", prompt.lower())


class TestValidateTranslationOutput(unittest.TestCase):

    def _write_temp(self, content: str, suffix: str = ".md") -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_valid_translation(self):
        source_text = (
            "# Title\n\nSome content here that is long enough to pass "
            "the minimum size check of one hundred bytes easily.\n\n"
            "## Section\n\nMore content with sufficient length.\n\n"
            "```yaml\nclaims:\n  - id: test\n```\n"
        )
        translation_text = (
            "# 제목\n\n최소 크기 검사를 통과할 만큼 충분히 긴 번역된 "
            "내용입니다. 이 내용은 테스트를 위한 것입니다.\n\n"
            "## 섹션\n\n충분한 길이의 추가 내용입니다.\n\n"
            "```yaml\nclaims:\n  - id: test\n```\n"
        )
        source = self._write_temp(source_text)
        translation = self._write_temp(translation_text)
        try:
            result = validate_translation_output(source, translation)
            self.assertTrue(result["l0"]["exists"])
            self.assertTrue(result["l0"]["size_ok"])
            self.assertTrue(result["structure"]["heading_match"])
            self.assertTrue(result["structure"]["code_blocks_preserved"])
        finally:
            os.unlink(source)
            os.unlink(translation)

    def test_missing_translation_file(self):
        source_text = (
            "# Title\n\nContent that is long enough to pass the "
            "minimum size validation check requirement.\n"
        )
        source = self._write_temp(source_text)
        try:
            result = validate_translation_output(source, "/nonexistent.ko.md")
            self.assertFalse(result["valid"])
            self.assertTrue(any("not found" in e for e in result["errors"]))
        finally:
            os.unlink(source)

    def test_heading_mismatch_detected(self):
        source_text = (
            "# H1 Title\n\nContent paragraph one with enough text.\n\n"
            "## H2 Section\n\nContent paragraph two.\n\n"
            "## H3 Another\n\nContent paragraph three with more text "
            "to ensure minimum size.\n"
        )
        translation_text = (
            "# 제목\n\n번역된 내용의 첫 번째 문단입니다.\n\n"
            "## 섹션\n\n두 번째 문단의 번역된 내용으로 최소 크기를 "
            "충족합니다.\n"
        )
        source = self._write_temp(source_text)
        translation = self._write_temp(translation_text)
        try:
            result = validate_translation_output(source, translation)
            self.assertFalse(result["structure"]["heading_match"])
            self.assertEqual(result["structure"]["source_headings"], 3)
            self.assertEqual(result["structure"]["translation_headings"], 2)
        finally:
            os.unlink(source)
            os.unlink(translation)

    def test_code_block_mismatch_detected(self):
        source_text = (
            "# Title\n\nSome content before code blocks that is long "
            "enough for minimum size validation.\n\n"
            "```python\nprint('hello')\n```\n\n"
            "Middle text between code blocks.\n\n"
            "```yaml\ndata: value\n```\n\nEnd text.\n"
        )
        translation_text = (
            "# 제목\n\n코드 블록 전의 내용으로 최소 크기 검증을 "
            "통과할 만큼 충분히 깁니다.\n\n"
            "```python\nprint('hello')\n```\n\n"
            "코드 블록 사이의 텍스트. 끝 텍스트.\n"
        )
        source = self._write_temp(source_text)
        translation = self._write_temp(translation_text)
        try:
            result = validate_translation_output(source, translation)
            self.assertFalse(result["structure"]["code_blocks_preserved"])
        finally:
            os.unlink(source)
            os.unlink(translation)

    def test_extreme_size_ratio_fails(self):
        source = self._write_temp("# Title\n" + "x" * 10000 + "\n")
        translation = self._write_temp("# 제목\nshort\n" + "y" * 150 + "\n")
        try:
            result = validate_translation_output(source, translation)
            self.assertFalse(result["valid"])
            self.assertTrue(any("ratio" in e for e in result["errors"]))
        finally:
            os.unlink(source)
            os.unlink(translation)


class TestExtractTranslationPacs(unittest.TestCase):

    def test_extract_all_four_dimensions(self):
        content = """
# Translation pACS Report

## Scores
| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Ft (Fidelity) | 85 | Good |
| Ct (Completeness) | 90 | Complete |
| Nt (Naturalness) | 80 | Natural |
| Tt (Theological Accuracy) | 88 | Accurate |

## Result: Translation pACS = 80 → GREEN
"""
        result = extract_translation_pacs(content)
        self.assertTrue(result["success"])
        self.assertEqual(result["scores"]["Ft"], 85)
        self.assertEqual(result["scores"]["Ct"], 90)
        self.assertEqual(result["scores"]["Nt"], 80)
        self.assertEqual(result["scores"]["Tt"], 88)
        self.assertEqual(result["pacs"], 80)
        self.assertEqual(result["grade"], "GREEN")
        self.assertEqual(result["weak_dimension"], "Nt")

    def test_yellow_grade(self):
        content = """
| Ft (Fidelity) | 65 | OK |
| Ct (Completeness) | 55 | Partial |
| Nt (Naturalness) | 70 | Good |
| Tt (Theological Accuracy) | 60 | Fair |
"""
        result = extract_translation_pacs(content)
        self.assertTrue(result["success"])
        self.assertEqual(result["pacs"], 55)
        self.assertEqual(result["grade"], "YELLOW")

    def test_red_grade(self):
        content = """
| Ft (Fidelity) | 40 | Poor |
| Ct (Completeness) | 45 | Missing |
| Nt (Naturalness) | 30 | Bad |
| Tt (Theological Accuracy) | 50 | Fair |
"""
        result = extract_translation_pacs(content)
        self.assertTrue(result["success"])
        self.assertEqual(result["pacs"], 30)
        self.assertEqual(result["grade"], "RED")
        self.assertEqual(result["weak_dimension"], "Nt")

    def test_missing_tt_succeeds_with_3_axes(self):
        """Tt is optional — 3-axis (Ft/Ct/Nt) pACS is valid for @translator."""
        content = """
| Ft (Fidelity) | 85 | Good |
| Ct (Completeness) | 90 | Good |
| Nt (Naturalness) | 80 | Good |
"""
        result = extract_translation_pacs(content)
        self.assertTrue(result["success"])
        self.assertEqual(result["pacs"], 80)
        self.assertEqual(result["scores"]["Tt"], 0)

    def test_missing_required_dimension_fails(self):
        """Missing Ft/Ct/Nt should still fail."""
        content = """
| Ft (Fidelity) | 85 | Good |
| Nt (Naturalness) | 80 | Good |
"""
        result = extract_translation_pacs(content)
        self.assertFalse(result["success"])
        self.assertIn("Ct", result["error"])

    def test_no_scores_fails(self):
        result = extract_translation_pacs("No scores here")
        self.assertFalse(result["success"])


class TestShouldRetranslate(unittest.TestCase):

    def test_green_no_retranslate(self):
        pacs = {"success": True, "pacs": 85, "grade": "GREEN",
                "weak_dimension": "Nt"}
        result = should_retranslate(pacs, retry_count=0)
        self.assertFalse(result["retranslate"])

    def test_yellow_no_retranslate(self):
        pacs = {"success": True, "pacs": 55, "grade": "YELLOW",
                "weak_dimension": "Ct"}
        result = should_retranslate(pacs, retry_count=0)
        self.assertFalse(result["retranslate"])
        self.assertIn("YELLOW", result["reason"])

    def test_red_triggers_retranslate(self):
        pacs = {"success": True, "pacs": 40, "grade": "RED",
                "weak_dimension": "Tt"}
        result = should_retranslate(pacs, retry_count=0)
        self.assertTrue(result["retranslate"])

    def test_red_max_retries_exhausted(self):
        pacs = {"success": True, "pacs": 40, "grade": "RED",
                "weak_dimension": "Tt"}
        result = should_retranslate(pacs, retry_count=2, max_retries=2)
        self.assertFalse(result["retranslate"])
        self.assertIn("exhausted", result["reason"])

    def test_extraction_failure_triggers_retranslate(self):
        pacs = {"success": False, "error": "No scores"}
        result = should_retranslate(pacs, retry_count=0)
        self.assertTrue(result["retranslate"])


class TestCollectDiscoveredTerms(unittest.TestCase):

    def _write_temp(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".ko.md")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_collect_terms_from_single_file(self):
        path = self._write_temp("""# 번역된 내용

## Discovered Terms
# New terms discovered during translation
- english: "kinsman-redeemer"
  korean: "기업 무를 자"
- english: "theophany"
  korean: "신현현(神顯現)"
""")
        try:
            terms = collect_discovered_terms([path])
            self.assertEqual(len(terms), 2)
            self.assertEqual(terms[0]["english"], "kinsman-redeemer")
            self.assertEqual(terms[1]["korean"], "신현현(神顯現)")
        finally:
            os.unlink(path)

    def test_deduplicates_across_files(self):
        p1 = self._write_temp('## Discovered Terms\n- english: "term"\n  korean: "용어"\n')
        p2 = self._write_temp('## Discovered Terms\n- english: "term"\n  korean: "다른용어"\n')
        try:
            terms = collect_discovered_terms([p1, p2])
            self.assertEqual(len(terms), 1)
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_no_terms_returns_empty(self):
        path = self._write_temp(
            "# 번역\n\n## Discovered Terms\n# No new terms discovered.\n")
        try:
            terms = collect_discovered_terms([path])
            self.assertEqual(terms, [])
        finally:
            os.unlink(path)

    def test_missing_file_skipped(self):
        terms = collect_discovered_terms(["/nonexistent.ko.md"])
        self.assertEqual(terms, [])


class TestMergeGlossaryTerms(unittest.TestCase):

    def _write_temp_glossary(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".yaml")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_add_new_terms(self):
        path = self._write_temp_glossary(
            '# Test glossary\n"existing": "기존"\n')
        try:
            new_terms = [{"english": "new-term", "korean": "새용어"}]
            result = merge_glossary_terms(path, new_terms)
            self.assertTrue(result["success"])
            self.assertEqual(result["added"], 1)
            self.assertEqual(result["skipped_duplicates"], 0)
            # Verify file content
            with open(path) as f:
                content = f.read()
            self.assertIn('"new-term": "새용어"', content)
            self.assertIn('"existing": "기존"', content)
        finally:
            os.unlink(path)

    def test_skip_duplicate_terms(self):
        path = self._write_temp_glossary('"existing": "기존"\n')
        try:
            new_terms = [{"english": "existing", "korean": "다른번역"}]
            result = merge_glossary_terms(path, new_terms)
            self.assertTrue(result["success"])
            self.assertEqual(result["added"], 0)
            self.assertEqual(result["skipped_duplicates"], 1)
        finally:
            os.unlink(path)

    def test_empty_terms_no_write(self):
        result = merge_glossary_terms("/any/path.yaml", [])
        self.assertTrue(result["success"])
        self.assertEqual(result["added"], 0)

    def test_atomic_write(self):
        """Verify .tmp file is used for atomic write."""
        path = self._write_temp_glossary('# glossary\n"a": "가"\n')
        try:
            new_terms = [{"english": "b", "korean": "나"}]
            result = merge_glossary_terms(path, new_terms)
            self.assertTrue(result["success"])
            # .tmp file should not exist after successful write
            self.assertFalse(os.path.exists(path + ".tmp"))
        finally:
            os.unlink(path)


class TestUpdateTranslationState(unittest.TestCase):
    """Tests for update_translation_state() — session.json translation tracking."""

    def _create_session(self, tmpdir, content=None):
        """Helper: create a session.json with optional content."""
        path = os.path.join(tmpdir, "session.json")
        if content is None:
            content = generate_session_json("passage", "Rom 8:1-10")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False)
        return path

    def test_basic_phase_completion(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._create_session(tmpdir)
            result = update_translation_state(path, "wave-1")
            self.assertTrue(result["success"])
            with open(path, "r") as f:
                session = json.load(f)
            self.assertIn("wave-1", session["translation_state"]["completed_phases"])

    def test_idempotent_phase_recording(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._create_session(tmpdir)
            update_translation_state(path, "wave-1")
            update_translation_state(path, "wave-1")  # duplicate
            with open(path, "r") as f:
                session = json.load(f)
            count = session["translation_state"]["completed_phases"].count("wave-1")
            self.assertEqual(count, 1)

    def test_glossary_terms_accumulate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._create_session(tmpdir)
            update_translation_state(path, "wave-1", glossary_terms_added=5)
            update_translation_state(path, "wave-2", glossary_terms_added=3)
            with open(path, "r") as f:
                session = json.load(f)
            self.assertEqual(session["translation_state"]["glossary_terms_added"], 8)
            self.assertIsNotNone(session["translation_state"]["glossary_updated_at"])

    def test_failed_translation_recorded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._create_session(tmpdir)
            result = update_translation_state(path, "wave-2", failed_file="03-structural-analysis.ko.md")
            self.assertTrue(result["success"])
            with open(path, "r") as f:
                session = json.load(f)
            failures = session["translation_state"]["failed_translations"]
            self.assertEqual(len(failures), 1)
            self.assertEqual(failures[0]["file"], "03-structural-analysis.ko.md")
            self.assertEqual(failures[0]["phase"], "wave-2")

    def test_backward_compat_v20_session(self):
        """v2.0 session.json without translation_state field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            v20 = {
                "version": "2.0",
                "mode": "passage",
                "input": "Psalm 23",
                "context_snapshots": {},
                "status": "initialized",
            }
            path = self._create_session(tmpdir, content=v20)
            result = update_translation_state(path, "wave-1", glossary_terms_added=2)
            self.assertTrue(result["success"])
            with open(path, "r") as f:
                session = json.load(f)
            self.assertIn("translation_state", session)
            self.assertIn("wave-1", session["translation_state"]["completed_phases"])
            self.assertEqual(session["translation_state"]["glossary_terms_added"], 2)

    def test_nonexistent_file_returns_error(self):
        result = update_translation_state("/nonexistent/path/session.json", "wave-1")
        self.assertFalse(result["success"])
        self.assertIsNotNone(result["error"])

    def test_multiple_phases_ordered(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._create_session(tmpdir)
            update_translation_state(path, "phase-0-a")
            update_translation_state(path, "wave-1")
            update_translation_state(path, "wave-2")
            with open(path, "r") as f:
                session = json.load(f)
            phases = session["translation_state"]["completed_phases"]
            self.assertEqual(phases, ["phase-0-a", "wave-1", "wave-2"])


# ===================================================================
# 14. Translation Orchestration — P1 Master Function Tests
# ===================================================================


class TestCheckPendingTranslation(unittest.TestCase):
    """Tests for check_pending_translation()."""

    def test_all_missing_returns_pending(self):
        result = check_pending_translation("wave-1", "/nonexistent/dir")
        self.assertTrue(result["pending"])
        self.assertEqual(result["total"], 4)
        self.assertEqual(len(result["missing_files"]), 4)
        self.assertEqual(len(result["existing_files"]), 0)
        self.assertEqual(result["phase"], "wave-1")

    def test_all_present_returns_not_pending(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = os.path.join(tmpdir, "research-package")
            os.makedirs(pkg)
            # Create all wave-1 .ko.md files
            for name in [
                "01-original-text-analysis.ko.md",
                "02-translation-manuscript-comparison.ko.md",
                "10-biblical-geography.ko.md",
                "11-historical-cultural-background.ko.md",
            ]:
                Path(os.path.join(pkg, name)).write_text("content", encoding="utf-8")

            result = check_pending_translation("wave-1", tmpdir)
            self.assertFalse(result["pending"])
            self.assertEqual(result["total"], 4)
            self.assertEqual(len(result["existing_files"]), 4)
            self.assertEqual(len(result["missing_files"]), 0)

    def test_partial_returns_pending(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = os.path.join(tmpdir, "research-package")
            os.makedirs(pkg)
            # Create only 2 of 4 wave-1 .ko.md files
            Path(os.path.join(pkg, "01-original-text-analysis.ko.md")).write_text(
                "content", encoding="utf-8"
            )
            Path(os.path.join(pkg, "10-biblical-geography.ko.md")).write_text(
                "content", encoding="utf-8"
            )

            result = check_pending_translation("wave-1", tmpdir)
            self.assertTrue(result["pending"])
            self.assertEqual(len(result["existing_files"]), 2)
            self.assertEqual(len(result["missing_files"]), 2)

    def test_unknown_phase_returns_not_pending(self):
        result = check_pending_translation("nonexistent-phase", "/out")
        self.assertFalse(result["pending"])
        self.assertEqual(result["total"], 0)

    def test_all_phases_covered(self):
        """Every TRANSLATION_TARGETS key works."""
        for phase in TRANSLATION_TARGETS:
            result = check_pending_translation(phase, "/nonexistent")
            self.assertEqual(result["phase"], phase)
            self.assertGreater(result["total"], 0)


class TestPrepareBatch(unittest.TestCase):
    """Tests for prepare_translation_batch()."""

    def test_unknown_phase_returns_skip(self):
        result = prepare_translation_batch("fake", "/out", "/g.yaml")
        self.assertIsNotNone(result["skip_reason"])
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["targets"], [])

    def test_already_complete_returns_skip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = os.path.join(tmpdir, "research-package")
            os.makedirs(pkg)
            # Create all wave-1 .ko.md files
            for name in [
                "01-original-text-analysis.ko.md",
                "02-translation-manuscript-comparison.ko.md",
                "10-biblical-geography.ko.md",
                "11-historical-cultural-background.ko.md",
            ]:
                Path(os.path.join(pkg, name)).write_text("ko", encoding="utf-8")

            result = prepare_translation_batch("wave-1", tmpdir, "/g.yaml")
            self.assertIsNotNone(result["skip_reason"])
            self.assertEqual(result["targets"], [])

    def test_generates_prompts_for_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = os.path.join(tmpdir, "research-package")
            os.makedirs(pkg)
            # Create English sources but no .ko.md
            for name in [
                "01-original-text-analysis.md",
                "02-translation-manuscript-comparison.md",
                "10-biblical-geography.md",
                "11-historical-cultural-background.md",
            ]:
                Path(os.path.join(pkg, name)).write_text(
                    "English content", encoding="utf-8"
                )

            glossary = os.path.join(tmpdir, "glossary.yaml")
            Path(glossary).write_text("# empty", encoding="utf-8")

            result = prepare_translation_batch("wave-1", tmpdir, glossary)
            self.assertIsNone(result["skip_reason"])
            self.assertEqual(result["total"], 4)
            self.assertEqual(len(result["targets"]), 4)

            # Each target must have prompt, source, target, pacs_log
            for t in result["targets"]:
                self.assertIn("source", t)
                self.assertIn("target", t)
                self.assertIn("prompt", t)
                self.assertIn("pacs_log", t)
                self.assertTrue(t["target"].endswith(".ko.md"))
                self.assertIn("Source File:", t["prompt"])

    def test_skips_existing_ko_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = os.path.join(tmpdir, "research-package")
            os.makedirs(pkg)
            # Create all English sources
            for name in [
                "01-original-text-analysis.md",
                "02-translation-manuscript-comparison.md",
                "10-biblical-geography.md",
                "11-historical-cultural-background.md",
            ]:
                Path(os.path.join(pkg, name)).write_text("EN", encoding="utf-8")
            # Create 2 .ko.md (already translated)
            Path(os.path.join(pkg, "01-original-text-analysis.ko.md")).write_text(
                "KO", encoding="utf-8"
            )
            Path(os.path.join(pkg, "10-biblical-geography.ko.md")).write_text(
                "KO", encoding="utf-8"
            )

            glossary = os.path.join(tmpdir, "g.yaml")
            Path(glossary).write_text("# g", encoding="utf-8")

            result = prepare_translation_batch("wave-1", tmpdir, glossary)
            # Only 2 targets should be generated (the missing ones)
            self.assertEqual(len(result["targets"]), 2)

    def test_skips_missing_english_source(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = os.path.join(tmpdir, "research-package")
            os.makedirs(pkg)
            # Create only 1 English source out of 4
            Path(os.path.join(pkg, "01-original-text-analysis.md")).write_text(
                "EN", encoding="utf-8"
            )
            glossary = os.path.join(tmpdir, "g.yaml")
            Path(glossary).write_text("# g", encoding="utf-8")

            result = prepare_translation_batch("wave-1", tmpdir, glossary)
            # Only 1 target (the one with English source)
            self.assertEqual(len(result["targets"]), 1)


class TestFinalizeBatch(unittest.TestCase):
    """Tests for finalize_translation_batch()."""

    def _create_session(self, tmpdir):
        path = os.path.join(tmpdir, "session.json")
        session = {
            "version": "2.1",
            "mode": "passage",
            "input": "test",
            "translation_state": {
                "completed_phases": [],
                "glossary_terms_added": 0,
                "glossary_updated_at": None,
                "failed_translations": [],
            },
        }
        with open(path, "w") as f:
            json.dump(session, f)
        return path

    def test_all_valid_translations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = os.path.join(tmpdir, "research-package")
            pacs_dir = os.path.join(tmpdir, "pacs-logs")
            os.makedirs(pkg)
            os.makedirs(pacs_dir)
            session = self._create_session(tmpdir)
            glossary = os.path.join(tmpdir, "glossary.yaml")
            Path(glossary).write_text("# empty glossary", encoding="utf-8")

            # Use phase-2-message (1 file) for simpler test
            source = os.path.join(tmpdir, "core-message.md")
            target = os.path.join(tmpdir, "core-message.ko.md")
            Path(source).write_text(
                "# Core Message\n\n" + "English content. " * 50,
                encoding="utf-8",
            )
            # Create valid translation with pACS scores
            ko_content = (
                "# 핵심 메시지\n\n"
                + "한국어 번역 내용입니다. " * 50
                + "\n\n## Scores\n"
                "| Dimension | Score |\n"
                "|-----------|-------|\n"
                "| Ft (Fidelity) | 90 |\n"
                "| Ct (Completeness) | 88 |\n"
                "| Nt (Naturalness) | 85 |\n"
                "| Tt (Theological Accuracy) | 92 |\n"
                "\n## Result: Translation pACS = 85\n"
                "\n## Discovered Terms\n"
                "# No new terms discovered.\n"
            )
            Path(target).write_text(ko_content, encoding="utf-8")

            result = finalize_translation_batch(
                "phase-2-message", tmpdir, glossary, session
            )

            self.assertEqual(len(result["results"]), 1)
            self.assertTrue(result["results"][0]["valid"])
            self.assertTrue(result["state_updated"])

    def test_missing_translation_triggers_retranslate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = os.path.join(tmpdir, "research-package")
            os.makedirs(pkg)
            session = self._create_session(tmpdir)
            glossary = os.path.join(tmpdir, "glossary.yaml")
            Path(glossary).write_text("# empty", encoding="utf-8")

            # Create English source but NO .ko.md
            source = os.path.join(tmpdir, "core-message.md")
            Path(source).write_text("# Core\n\nContent", encoding="utf-8")

            result = finalize_translation_batch(
                "phase-2-message", tmpdir, glossary, session
            )

            self.assertFalse(result["all_valid"])
            self.assertGreater(len(result["retranslate"]), 0)
            # retranslate entry has prompt
            self.assertIn("prompt", result["retranslate"][0])

    def test_state_updated_with_phase(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = self._create_session(tmpdir)
            glossary = os.path.join(tmpdir, "glossary.yaml")
            Path(glossary).write_text("# empty", encoding="utf-8")

            # Even with no files, state should be updated
            finalize_translation_batch(
                "phase-2-message", tmpdir, glossary, session
            )

            with open(session, "r") as f:
                data = json.load(f)
            self.assertIn(
                "phase-2-message",
                data["translation_state"]["completed_phases"],
            )


# ===================================================================
# 15. Session Discovery & Context Resolution Tests
# ===================================================================


class TestCreateOutputStructureCollision(unittest.TestCase):
    """Test collision avoidance in create_output_structure."""

    def test_no_collision(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = os.path.join(tmpdir, "my-sermon-2026-03-06")
            dirs = create_output_structure(base)
            self.assertEqual(dirs["root"], base)
            self.assertTrue(os.path.isdir(base))

    def test_collision_appends_suffix(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = os.path.join(tmpdir, "my-sermon-2026-03-06")
            os.makedirs(base)  # Pre-create to force collision
            dirs = create_output_structure(base)
            self.assertEqual(dirs["root"], f"{base}-2")
            self.assertTrue(os.path.isdir(f"{base}-2"))

    def test_multiple_collisions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = os.path.join(tmpdir, "my-sermon-2026-03-06")
            os.makedirs(base)
            os.makedirs(f"{base}-2")
            os.makedirs(f"{base}-3")
            dirs = create_output_structure(base)
            self.assertEqual(dirs["root"], f"{base}-4")

    def test_pacs_logs_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = os.path.join(tmpdir, "test-output")
            dirs = create_output_structure(base)
            self.assertIn("pacs_logs", dirs)
            self.assertTrue(os.path.isdir(dirs["pacs_logs"]))


class TestInitializeSermonOutput(unittest.TestCase):
    """Test P1 Master: initialize_sermon_output."""

    def test_basic_initialization(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch get_output_dir_name to use tmpdir
            original = get_output_dir_name("Romans 8:1-10")
            base_in_tmp = os.path.join(tmpdir, os.path.basename(original))

            # We can't easily mock get_output_dir_name, so test via
            # create_output_structure + session + checklist correctness
            result = initialize_sermon_output(
                "Romans 8:1-10", "passage"
            )
            self.assertTrue(result["success"])
            self.assertTrue(result["output_dir"].startswith("sermon-output/"))
            self.assertTrue(os.path.isfile(result["session_path"]))
            self.assertTrue(os.path.isfile(result["checklist_path"]))

            # Verify session.json content
            with open(result["session_path"], "r") as f:
                session = json.load(f)
            self.assertEqual(session["mode"], "passage")
            self.assertEqual(session["input"], "Romans 8:1-10")

            # Verify state_yaml_sermon
            sym = result["state_yaml_sermon"]
            self.assertEqual(sym["mode"], "passage")
            self.assertEqual(sym["output_dir"], result["output_dir"])
            self.assertEqual(sym["completed_gates"], [])
            self.assertEqual(sym["srcs_threshold"], 70)

            # Cleanup
            import shutil
            shutil.rmtree(result["output_dir"], ignore_errors=True)

    def test_invalid_mode_defaults(self):
        result = initialize_sermon_output("test input", "invalid_mode")
        self.assertTrue(result["success"])
        self.assertEqual(result["state_yaml_sermon"]["mode"], "theme")
        import shutil
        shutil.rmtree(result["output_dir"], ignore_errors=True)

    def test_checklist_has_content(self):
        result = initialize_sermon_output("Psalm 23:1-6", "passage")
        self.assertTrue(result["success"])
        with open(result["checklist_path"], "r") as f:
            content = f.read()
        self.assertIn("Step 1:", content)
        import shutil
        shutil.rmtree(result["output_dir"], ignore_errors=True)


class TestFindActiveSession(unittest.TestCase):
    """Test fallback session scanner."""

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = find_active_session(tmpdir)
            self.assertFalse(result["found"])

    def test_nonexistent_directory(self):
        result = find_active_session("/nonexistent/path")
        self.assertFalse(result["found"])

    def test_finds_running_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d1 = os.path.join(tmpdir, "sermon-1")
            os.makedirs(d1)
            with open(os.path.join(d1, "session.json"), "w") as f:
                json.dump({
                    "status": "running",
                    "created_at": "2026-03-06T10:00:00+00:00",
                }, f)

            result = find_active_session(tmpdir)
            self.assertTrue(result["found"])
            self.assertEqual(result["status"], "running")
            self.assertEqual(result["session_dir"], d1)

    def test_prefers_running_over_completed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Completed session (newer)
            d1 = os.path.join(tmpdir, "sermon-1")
            os.makedirs(d1)
            with open(os.path.join(d1, "session.json"), "w") as f:
                json.dump({
                    "status": "completed",
                    "created_at": "2026-03-06T12:00:00+00:00",
                }, f)

            # Running session (older)
            d2 = os.path.join(tmpdir, "sermon-2")
            os.makedirs(d2)
            with open(os.path.join(d2, "session.json"), "w") as f:
                json.dump({
                    "status": "running",
                    "created_at": "2026-03-06T10:00:00+00:00",
                }, f)

            result = find_active_session(tmpdir)
            self.assertTrue(result["found"])
            self.assertEqual(result["status"], "running")
            self.assertEqual(result["session_dir"], d2)

    def test_all_completed_returns_most_recent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d1 = os.path.join(tmpdir, "sermon-1")
            os.makedirs(d1)
            with open(os.path.join(d1, "session.json"), "w") as f:
                json.dump({
                    "status": "completed",
                    "created_at": "2026-03-05T10:00:00+00:00",
                }, f)

            d2 = os.path.join(tmpdir, "sermon-2")
            os.makedirs(d2)
            with open(os.path.join(d2, "session.json"), "w") as f:
                json.dump({
                    "status": "completed",
                    "created_at": "2026-03-06T10:00:00+00:00",
                }, f)

            result = find_active_session(tmpdir)
            self.assertTrue(result["found"])
            self.assertEqual(result["session_dir"], d2)

    def test_ignores_corrupt_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            d1 = os.path.join(tmpdir, "sermon-1")
            os.makedirs(d1)
            with open(os.path.join(d1, "session.json"), "w") as f:
                f.write("{corrupt json")

            d2 = os.path.join(tmpdir, "sermon-2")
            os.makedirs(d2)
            with open(os.path.join(d2, "session.json"), "w") as f:
                json.dump({
                    "status": "running",
                    "created_at": "2026-03-06T10:00:00+00:00",
                }, f)

            result = find_active_session(tmpdir)
            self.assertTrue(result["found"])
            self.assertEqual(result["session_dir"], d2)


class TestBuildSermonPathMap(unittest.TestCase):
    """Test deterministic path map builder."""

    def test_all_paths_present(self):
        paths = _build_sermon_path_map("sermon-output/test-2026-03-06")
        expected_keys = {
            "session_json", "checklist",
            "research_synthesis", "research_synthesis_ko",
            "core_message", "core_message_ko",
            "sermon_outline", "sermon_outline_ko",
            "sermon_draft", "sermon_draft_ko",
            "sermon_final", "sermon_final_ko",
            "review_report", "review_report_ko",
            "research_package", "pacs_logs",
        }
        self.assertEqual(set(paths.keys()), expected_keys)

    def test_paths_use_output_dir(self):
        paths = _build_sermon_path_map("sermon-output/my-sermon-2026-03-06")
        for key, path in paths.items():
            self.assertTrue(
                path.startswith("sermon-output/my-sermon-2026-03-06"),
                f"{key}: {path} does not start with expected prefix",
            )

    def test_ko_files_have_ko_extension(self):
        paths = _build_sermon_path_map("sermon-output/test")
        ko_keys = [k for k in paths if k.endswith("_ko")]
        for k in ko_keys:
            self.assertIn(".ko.", paths[k])


class TestResolveSermonContext(unittest.TestCase):
    """Test P1 Master: resolve_sermon_context."""

    def _create_session_dir(self, tmpdir, name, status="running"):
        """Helper: create a minimal sermon output directory."""
        d = os.path.join(tmpdir, "sermon-output", name)
        os.makedirs(os.path.join(d, "research-package"), exist_ok=True)

        session = {
            "version": "2.1",
            "created_at": "2026-03-06T04:21:24+00:00",
            "mode": "passage",
            "input": "Romans 8:1-10",
            "status": status,
            "translation_state": {
                "completed_phases": ["wave-1"],
                "glossary_terms_added": 5,
                "glossary_updated_at": None,
                "failed_translations": [],
            },
        }
        with open(os.path.join(d, "session.json"), "w") as f:
            json.dump(session, f)

        # Minimal checklist
        with open(os.path.join(d, "todo-checklist.md"), "w") as f:
            f.write("## Phase 0\n- [x] Step 1: Init\n- [ ] Step 2: Next\n")

        return d

    def test_resolve_via_state_yaml(self):
        """Normal flow: state.yaml points to correct output_dir."""
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            sermon_dir = self._create_session_dir(tmpdir, "Romans-8-1-10-2026-03-06")

            # Write state.yaml
            state_yaml = os.path.join(tmpdir, "state.yaml")
            with open(state_yaml, "w") as f:
                yaml.dump({
                    "workflow": {
                        "name": "sermon-research",
                        "sermon": {"output_dir": sermon_dir},
                    }
                }, f)

            result = resolve_sermon_context(
                state_yaml_path=state_yaml,
                fallback_base=os.path.join(tmpdir, "sermon-output"),
            )
            self.assertTrue(result["found"])
            self.assertEqual(result["output_dir"], sermon_dir)
            self.assertEqual(result["source"], "state_yaml")
            self.assertEqual(result["session"]["mode"], "passage")
            self.assertIn("wave-1", result["translation_state"]["completed_phases"])
            self.assertEqual(result["progress"]["completed"], 1)

    def test_resolve_via_fallback(self):
        """Fallback flow: no state.yaml, scan directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sermon_dir = self._create_session_dir(tmpdir, "Romans-8-1-10-2026-03-06")

            result = resolve_sermon_context(
                state_yaml_path=os.path.join(tmpdir, "nonexistent-state.yaml"),
                fallback_base=os.path.join(tmpdir, "sermon-output"),
            )
            self.assertTrue(result["found"])
            self.assertEqual(result["output_dir"], sermon_dir)
            self.assertEqual(result["source"], "fallback_scan")

    def test_no_session_found(self):
        """Error: neither state.yaml nor session.json exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = resolve_sermon_context(
                state_yaml_path=os.path.join(tmpdir, "nonexistent.yaml"),
                fallback_base=os.path.join(tmpdir, "empty"),
            )
            self.assertFalse(result["found"])
            self.assertIsNotNone(result["error"])

    def test_paths_map_populated(self):
        """Verify that paths map contains all expected keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sermon_dir = self._create_session_dir(tmpdir, "test-2026-03-06")

            result = resolve_sermon_context(
                state_yaml_path=os.path.join(tmpdir, "none.yaml"),
                fallback_base=os.path.join(tmpdir, "sermon-output"),
            )
            self.assertTrue(result["found"])
            self.assertIn("sermon_final", result["paths"])
            self.assertIn("research_package", result["paths"])
            self.assertTrue(
                result["paths"]["session_json"].endswith("session.json")
            )


if __name__ == "__main__":
    unittest.main()
