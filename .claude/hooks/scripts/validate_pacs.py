#!/usr/bin/env python3
"""
pACS Log P1 Validation — validate_pacs.py

Standalone script called by Orchestrator after pACS scoring completes.
NOT a Hook — manually invoked during workflow execution.

Usage:
    python3 .claude/hooks/scripts/validate_pacs.py --step 3 --project-dir .
    python3 .claude/hooks/scripts/validate_pacs.py --step 3 --type translation --project-dir .
    python3 .claude/hooks/scripts/validate_pacs.py --step 3 --check-l0 --project-dir .

Output: JSON to stdout
    {"valid": true, "warnings": [], ...}

Exit codes:
    0 — validation completed (check "valid" field for result)
    1 — argument error or fatal failure

Checks (PA1-PA4 + T9 + PA7):
    PA1: pACS log file exists
    PA2: Minimum file size (≥ 50 bytes)
    PA3: Dimension scores present (≥ 3 dimensions, each 0-100)
    PA4: Pre-mortem section present (mandatory before scoring)
    PA5/T9: pACS = min(dimensions) arithmetic correctness
           (delegates to verify_pacs_arithmetic → emits "T9 FAIL:" prefix)

Optional:
    PA6: Color zone validation (score vs declared RED/YELLOW/GREEN)
    --check-l0: Also validate step output (L0 Anti-Skip Guard)

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
    validate_pacs_output,
    validate_step_output,
)


def main():
    parser = argparse.ArgumentParser(
        description="P1 Validation for pACS scoring outputs"
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
        "--type", type=str, default="general",
        choices=["general", "translation", "review"],
        help="pACS log type (default: general)"
    )
    parser.add_argument(
        "--check-l0", action="store_true",
        help="Also validate step output via L0 Anti-Skip Guard"
    )
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    step = args.step

    # Core validation: PA1-PA6
    is_valid, warnings = validate_pacs_output(project_dir, step, pacs_type=args.type)

    # Remediation mapping — OpenAI harness pattern: inject fix instructions
    _REMEDIATIONS = {
        "PA1": f"Generate pACS log: run Pre-mortem Protocol → F/C/L scoring → save to pacs-logs/step-{step}-pacs.md",
        "PA2": "pACS log is too small — include Pre-mortem 3 questions + all dimension scores + pACS = min(F,C,L)",
        "PA3": "Add dimension scores: F (Faithfulness), C (Completeness), L (Lucidity) each 0-100",
        "PA4": "Add Pre-mortem section before scores — answer 3 questions per AGENTS.md §5.4",
        "T9": "Fix pACS arithmetic: pACS must equal min(all dimension scores). Check pACS log for correct dimension names (F/C/L or Ft/Ct/Nt/Tt)",
        "PA7": f"pACS is RED (< 50) — rework required. Run: python3 .claude/hooks/scripts/validate_retry_budget.py --step {step} --gate pacs --project-dir . --check-and-increment",
        # L0 Anti-Skip Guard remediations (used when --check-l0 is active)
        "L0a": f"Step {step} output file missing — ensure SOT outputs.step-{step} points to an existing file",
        "L0b": f"Step {step} output file too small (< 100 bytes) — produce complete output before advancing",
        "L0c": f"Step {step} output file is empty/whitespace-only — generate substantive content",
    }

    # Build output
    output = {
        "valid": is_valid,
        "step": step,
        "pacs_type": args.type,
        "warnings": list(warnings),
    }

    # Extract remediation for failed checks (P1-B: central function + P1-F: self-check)
    remediations = extract_remediations(warnings, _REMEDIATIONS)
    if remediations:
        output["remediations"] = remediations

    # Optional: L0 Anti-Skip Guard
    if args.check_l0:
        l0_valid, l0_warnings = validate_step_output(project_dir, step)
        output["l0_valid"] = l0_valid
        output["l0_warnings"] = list(l0_warnings)
        if not l0_valid:
            output["valid"] = False
        # L0 remediation extraction (L0a/L0b/L0c keys in _REMEDIATIONS)
        l0_remediations = extract_remediations(l0_warnings, _REMEDIATIONS)
        if l0_remediations:
            existing = output.get("remediations", {})
            existing.update(l0_remediations)
            output["remediations"] = existing

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
