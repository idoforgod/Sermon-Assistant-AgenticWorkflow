#!/usr/bin/env python3
"""
Translation P1 Validation — validate_translation.py

Standalone script called by Orchestrator after translator sub-agent completes.
NOT a Hook — manually invoked during workflow execution.

Usage:
    python3 .claude/hooks/scripts/validate_translation.py --step 3 --project-dir .

Output: JSON to stdout
    {"valid": true, "warnings": [], "glossary_valid": true, ...}

Exit codes:
    0 — validation completed (check "valid" field for result)
    1 — argument error or fatal failure

P1 Compliance: All validation is deterministic (delegates to _context_lib).
SOT Compliance: Read-only — no file writes.
"""

import argparse
import json
import os
import sys

# Add script directory to path for shared library import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _context_lib import (
    extract_remediations,
    validate_translation_output,
    check_glossary_freshness,
    verify_pacs_arithmetic,
    validate_review_sequence,
    parse_review_verdict,
)


def main():
    parser = argparse.ArgumentParser(
        description="P1 Validation for Translation outputs"
    )
    parser.add_argument(
        "--step", type=int, required=True,
        help="Step number to validate"
    )
    parser.add_argument(
        "--project-dir", type=str, default=".",
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--check-sequence", action="store_true",
        help="Also validate review→translation sequence (T8 + timestamp)"
    )
    parser.add_argument(
        "--check-pacs", action="store_true",
        help="Also validate translation pACS arithmetic (T9)"
    )
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    step = args.step

    # Core validation: T1-T7
    is_valid, warnings = validate_translation_output(project_dir, step)

    # Mandatory: Review verdict PASS check (autopilot-execution.md NEVER DO — Review FAIL 상태에서 Translation 금지)
    # This runs unconditionally, unlike --check-sequence which also checks timestamps.
    review_path = os.path.join(
        project_dir, "review-logs", f"step-{step}-review.md"
    )
    if os.path.exists(review_path):
        verdict_data = parse_review_verdict(review_path)
        if verdict_data["verdict"] and verdict_data["verdict"] != "PASS":
            is_valid = False
            warnings = list(warnings)
            warnings.append(
                f"RV1 FAIL: Review verdict is {verdict_data['verdict']} — must be PASS before translation"
            )

    # T8: Glossary freshness
    glossary_valid, glossary_warning = check_glossary_freshness(project_dir, step)

    # Remediation mapping — OpenAI harness pattern: inject fix instructions
    _REMEDIATIONS = {
        "T1": f"Create translation file: invoke @translator sub-agent → save to translations/step-{step}.ko.md",
        "T2": "Translation file is too small — @translator must produce complete translation, not stub",
        "T3": f"English source file missing — ensure step {step} output exists before translating",
        "T4": "Translation file must have .ko.md extension (e.g., step-3.ko.md)",
        "T5": "Translation file is empty or whitespace-only — re-run @translator",
        "T6": "Heading count mismatch: Korean translation headings differ > 20% from English source — check for missing/extra sections",
        "T7": "Code block count mismatch: Korean translation must preserve all code blocks from English source",
        "T8": "Glossary is stale — update translations/glossary.yaml with terms from this step",
        "T9": "Fix translation pACS arithmetic: pACS must equal min(Ft, Ct, Nt, Tt). Recalculate and correct",
        "RV1": "Review verdict must be PASS before translation — fix review issues first, re-run @reviewer, then translate",
    }

    # Build output
    output = {
        "valid": is_valid and glossary_valid,
        "step": step,
        "translation_valid": is_valid,
        "glossary_valid": glossary_valid,
        "warnings": list(warnings),  # ensure list copy
    }

    # Extract remediation for failed checks (P1-B: central function + P1-F: self-check)
    remediations = extract_remediations(warnings, _REMEDIATIONS)
    if remediations:
        output["remediations"] = remediations

    if glossary_warning:
        output["glossary_warning"] = glossary_warning
        output["warnings"].append(glossary_warning)

    # Optional: T9 — pACS arithmetic check
    if args.check_pacs:
        pacs_path = os.path.join(
            project_dir, "pacs-logs", f"step-{step}-translation-pacs.md"
        )
        pacs_valid, pacs_warning = verify_pacs_arithmetic(pacs_path)
        output["pacs_arithmetic_valid"] = pacs_valid
        if pacs_warning:
            output["pacs_arithmetic_warning"] = pacs_warning
            output["warnings"].append(pacs_warning)
            if not pacs_valid:
                output["valid"] = False

    # Optional: sequence validation (review PASS before translation)
    if args.check_sequence:
        seq_valid, seq_warning = validate_review_sequence(project_dir, step)
        output["sequence_valid"] = seq_valid
        if seq_warning:
            output["sequence_warning"] = seq_warning
            output["warnings"].append(seq_warning)
            if not seq_valid:
                output["valid"] = False

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_output = {
            "valid": False,
            "error": str(e),
            "warnings": [f"Fatal error: {e}"],
        }
        print(json.dumps(error_output, indent=2, ensure_ascii=False))
        sys.exit(1)
