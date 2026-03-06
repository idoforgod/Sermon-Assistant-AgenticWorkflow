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
        # workflow.md table (lines 1084-1099) sums to exactly 130
        self.assertEqual(total, 130)

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
        # Wave 1 starts after Phase 0 (6) + Phase 0-A (6) + HITL-1 (3) = step 16
        wave = get_current_wave(16)
        self.assertEqual(wave, "wave-1")

    def test_check_pending_gate_none(self):
        result = check_pending_gate(1, [])
        self.assertIsNone(result)

    def test_check_pending_gate_detected(self):
        # Wave 1 ends at step 6+6+3+16 = 31, gate-1 fires after step 31
        # Step 32 is past wave-1 end, so gate-1 should be pending
        result = check_pending_gate(32, [])
        self.assertEqual(result, "gate-1")

    def test_check_pending_gate_completed(self):
        result = check_pending_gate(32, ["gate-1"])
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


if __name__ == "__main__":
    unittest.main()
