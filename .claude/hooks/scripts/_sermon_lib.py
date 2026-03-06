#!/usr/bin/env python3
"""
Sermon Research Workflow — Deterministic Library
=================================================

P1 Compliance: All functions are deterministic. Zero AI judgment.
SOT Compliance: state.yaml read-only (writes are Orchestrator's job).
_context_lib.py Independence: Zero imports from _context_lib.py. Zero coupling.

Functions grouped by domain:
  1. Schema Validation (GroundedClaim, SRCS output, sermon SOT schema)
  2. Hallucination Firewall (regex-based pattern blocking)
  3. SRCS Scoring (4-axis mathematical calculation)
  4. Cross-Validation Gate (structural validation only)
  5. Checklist Management (155-step todo-checklist.md per workflow.md table)
  6. Session Initialization (Phase 0 deterministic setup)
  7. Error Handling (agent-level 5 types + workflow-level 3 handlers)
  8-10. Wave boundary, utility, formatting
  11. Agent Dispatch (dependency resolution + prompt generation)
  12. Agent Output Validation (P1 claim extraction + unified pipeline)
  13. Gate Completion (safe SOT update with ordering enforcement)
  14. Translation Management (P1 routing, prompt, validation, pACS, glossary)
  15. Session Discovery & Context Resolution (P1 Masters for init/resume)

Reference: prompt/workflow.md (Sermon Research Workflow v2.0)
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ===================================================================
# 1. CONSTANTS — Single Definition Point
# ===================================================================

VALID_CLAIM_TYPES = {
    "FACTUAL", "LINGUISTIC", "HISTORICAL",
    "THEOLOGICAL", "INTERPRETIVE", "APPLICATIONAL",
}

VALID_SOURCE_TYPES = {"PRIMARY", "SECONDARY", "TERTIARY"}

# ClaimType → (required source types, minimum count)
CLAIM_TYPE_SOURCE_REQUIREMENTS: dict[str, tuple[set[str], int]] = {
    "FACTUAL":       ({"PRIMARY", "SECONDARY"}, 1),
    "LINGUISTIC":    ({"PRIMARY"}, 1),
    "HISTORICAL":    ({"SECONDARY", "TERTIARY"}, 1),
    "THEOLOGICAL":   ({"SECONDARY", "TERTIARY"}, 1),
    "INTERPRETIVE":  (set(), 0),
    "APPLICATIONAL": (set(), 0),
}

# ClaimType → minimum expected confidence
CONFIDENCE_THRESHOLDS: dict[str, int] = {
    "FACTUAL": 95, "LINGUISTIC": 90, "HISTORICAL": 80,
    "THEOLOGICAL": 70, "INTERPRETIVE": 70, "APPLICATIONAL": 60,
}

# ClaimType → SRCS weight distribution {CS, GS, US, VS}
# FACTUAL weights from workflow.md:643-648.
# Non-FACTUAL weights are implementation-defined extensions following the
# principle: higher subjectivity → lower CS/GS, higher US/VS.
SRCS_WEIGHTS: dict[str, dict[str, float]] = {
    "FACTUAL":       {"CS": 0.3, "GS": 0.4, "US": 0.1, "VS": 0.2},
    "LINGUISTIC":    {"CS": 0.35, "GS": 0.35, "US": 0.1, "VS": 0.2},
    "HISTORICAL":    {"CS": 0.25, "GS": 0.35, "US": 0.2, "VS": 0.2},
    "THEOLOGICAL":   {"CS": 0.2, "GS": 0.3, "US": 0.3, "VS": 0.2},
    "INTERPRETIVE":  {"CS": 0.15, "GS": 0.25, "US": 0.35, "VS": 0.25},
    "APPLICATIONAL": {"CS": 0.1, "GS": 0.2, "US": 0.3, "VS": 0.4},
}

# Valid agent claim prefixes (workflow.md:754-815)
AGENT_CLAIM_PREFIXES: dict[str, str] = {
    "original-text-analyst": "OTA",
    "manuscript-comparator": "MC",
    "structure-analyst": "SA",
    "parallel-passage-analyst": "PPA",
    "theological-analyst": "TA",
    "literary-analyst": "LA",
    "rhetorical-analyst": "RA",
    "historical-context-analyst": "HCA",
    "keyword-expert": "KWE",
    "biblical-geography-expert": "BGE",
    "historical-cultural-expert": "HCE",
}

# Wave definitions (workflow.md:172-198)
WAVE_AGENTS: dict[str, list[str]] = {
    "wave-1": [
        "original-text-analyst", "manuscript-comparator",
        "biblical-geography-expert", "historical-cultural-expert",
    ],
    "wave-2": [
        "structure-analyst", "parallel-passage-analyst", "keyword-expert",
    ],
    "wave-3": [
        "theological-analyst", "literary-analyst", "historical-context-analyst",
    ],
    "wave-4": ["rhetorical-analyst"],
}

# Wave gate boundaries: gate N validates the preceding wave's agents
WAVE_GATE_MAP: dict[str, list[str]] = {
    "gate-1": WAVE_AGENTS["wave-1"],
    "gate-2": WAVE_AGENTS["wave-2"],
    "gate-3": WAVE_AGENTS["wave-3"],
}

# Agent output file mapping (workflow.md:709-720)
AGENT_OUTPUT_FILES: dict[str, str] = {
    "original-text-analyst": "01-original-text-analysis.md",
    "manuscript-comparator": "02-translation-manuscript-comparison.md",
    "structure-analyst": "03-structural-analysis.md",
    "parallel-passage-analyst": "04-parallel-passage-analysis.md",
    "theological-analyst": "05-theological-analysis.md",
    "literary-analyst": "06-literary-analysis.md",
    "rhetorical-analyst": "07-rhetorical-analysis.md",
    "historical-context-analyst": "08-historical-cultural-context.md",
    "keyword-expert": "09-keyword-study.md",
    "biblical-geography-expert": "10-biblical-geography.md",
    "historical-cultural-expert": "11-historical-cultural-background.md",
}

# Agent dependency graph (workflow.md:765-808)
# Key = agent, Value = list of upstream agents whose output must be read first
AGENT_DEPENDENCIES: dict[str, list[str]] = {
    # Wave 1: independent (no dependencies)
    "original-text-analyst": [],
    "manuscript-comparator": [],
    "biblical-geography-expert": [],
    "historical-cultural-expert": [],
    # Wave 2: depends on Wave 1
    "structure-analyst": ["original-text-analyst"],
    "parallel-passage-analyst": ["original-text-analyst"],
    "keyword-expert": ["original-text-analyst"],
    # Wave 3: depends on Wave 2 (or Wave 1 for historical-context-analyst)
    "theological-analyst": ["structure-analyst"],
    "literary-analyst": ["structure-analyst"],
    "historical-context-analyst": ["historical-cultural-expert"],
    # Wave 4: depends on Wave 3
    "rhetorical-analyst": ["literary-analyst"],
}

# Failure types (workflow.md:689-699)
FAILURE_TYPES = {
    "LOOP_EXHAUSTED", "SOURCE_UNAVAILABLE", "INPUT_INVALID",
    "CONFLICT_UNRESOLVABLE", "OUT_OF_SCOPE",
}

# Hallucination Firewall patterns (workflow.md:631-639)
# Compiled once at module level for performance
_FIREWALL_BLOCK = [
    re.compile(r"\b(all|every)\s+scholars?\s+(agree|consensus)", re.IGNORECASE),
    re.compile(r"\b100\s*%\s*(certain|sure|accurate)", re.IGNORECASE),
    re.compile(r"\bwithout\s+(any\s+)?exception", re.IGNORECASE),
    re.compile(r"\buniversally\s+accepted", re.IGNORECASE),
    re.compile(r"\bno\s+scholar\s+disagrees", re.IGNORECASE),
    # Korean equivalents
    re.compile(r"모든\s*학자(들이|가)\s*(동의|합의)"),
    re.compile(r"예외\s*없이"),
    re.compile(r"보편적으로\s*인정"),
    re.compile(r"반론(의\s*여지가|이)\s*없"),
]

_FIREWALL_REQUIRE_SOURCE = [
    re.compile(r"\bexactly\s+\d+", re.IGNORECASE),
    re.compile(r"\b(BC|BCE)\s+\d{3,4}\b"),
    re.compile(r"\b\d{3,4}\s*(BC|BCE)\b"),
    re.compile(r"\bprecisely\s+\d+", re.IGNORECASE),
]

_FIREWALL_SOFTEN = [
    re.compile(r"\bcertainly\b", re.IGNORECASE),
    re.compile(r"\bclearly\b", re.IGNORECASE),
    re.compile(r"\bobviously\b", re.IGNORECASE),
    re.compile(r"\bundeniably\b", re.IGNORECASE),
    re.compile(r"\bundoubtedly\b", re.IGNORECASE),
]

_FIREWALL_VERIFY = [
    re.compile(r"\b(Dr|Prof)\.?\s+[A-Z]\w+\s+(argues?|claims?|states?)",
               re.IGNORECASE),
    re.compile(r"\btraditionally\b", re.IGNORECASE),
    re.compile(r"\baccording\s+to\s+tradition", re.IGNORECASE),
]

# Input mode patterns (workflow.md:92-97)
INPUT_MODES = {"theme", "passage", "series"}

# Translation target files per phase/wave (P1 deterministic routing)
# Key = phase/wave, Value = list of files to translate after that phase
TRANSLATION_TARGETS: dict[str, list[str]] = {
    "phase-0-a": ["passage-candidates.md"],
    "phase-0-c": ["series-context.md"],
    "wave-1": [
        "01-original-text-analysis.md",
        "02-translation-manuscript-comparison.md",
        "10-biblical-geography.md",
        "11-historical-cultural-background.md",
    ],
    "wave-2": [
        "03-structural-analysis.md",
        "04-parallel-passage-analysis.md",
        "09-keyword-study.md",
    ],
    "wave-3": [
        "05-theological-analysis.md",
        "06-literary-analysis.md",
        "08-historical-cultural-context.md",
    ],
    "wave-4": [
        "07-rhetorical-analysis.md",
        "confidence-report.md",
        "research-synthesis.md",
    ],
    "phase-2-message": ["core-message.md"],
    "phase-2-outline": ["sermon-outline.md"],
    "phase-3-draft": ["sermon-draft.md"],
    "phase-3-review": ["review-report.md"],
    "phase-3-final": ["sermon-final.md"],
}

# Checklist template section counts (workflow.md:1084-1099 table, updated for translation)
# Total: 155 steps (130 original + 25 translation steps)
CHECKLIST_SECTIONS = [
    ("Phase 0: Initialization", 6),
    ("Phase 0-A: Passage Search (Mode A)", 8),
    ("HITL-1: Passage Selection", 3),
    ("Wave 1: Independent Analysis", 16),
    ("Wave 1 Translation", 4),
    ("Wave 2: Dependent Analysis", 12),
    ("Wave 2 Translation", 3),
    ("Wave 3: Deep Analysis", 12),
    ("Wave 3 Translation", 3),
    ("Wave 4: Integration Analysis", 6),
    ("Wave 4 Translation", 3),
    ("HITL-2: Research Review", 8),
    ("Phase 2: Planning", 20),
    ("HITL-3a/3b: Style & Message", 10),
    ("Phase 2.5: Style Analysis", 4),
    ("HITL-4: Outline Approval", 3),
    ("Phase 3: Implementation", 24),
    ("HITL-5a/5b: Format & Final", 10),
]


# ===================================================================
# 2. SCHEMA VALIDATION — GroundedClaim
# ===================================================================

def validate_grounded_claim(claim: dict[str, Any]) -> list[str]:
    """Validate a single GroundedClaim against the schema.

    Returns list of error messages. Empty list = valid.

    Schema (workflow.md:603-617):
      id: str (prefix-NNN)
      text: str (non-empty)
      claim_type: one of VALID_CLAIM_TYPES
      sources: list of {type, reference, verified}
      confidence: int 0-100
      uncertainty: str or null
    """
    errors: list[str] = []
    claim_id = claim.get("id", "<missing>")

    # id
    if "id" not in claim:
        errors.append("missing required field: id")
    elif not isinstance(claim["id"], str) or not claim["id"].strip():
        errors.append("id must be a non-empty string")

    # text
    if "text" not in claim:
        errors.append(f"[{claim_id}] missing required field: text")
    elif not isinstance(claim["text"], str) or not claim["text"].strip():
        errors.append(f"[{claim_id}] text must be a non-empty string")

    # claim_type
    ct = claim.get("claim_type")
    if ct is None:
        errors.append(f"[{claim_id}] missing required field: claim_type")
    elif ct not in VALID_CLAIM_TYPES:
        errors.append(
            f"[{claim_id}] invalid claim_type '{ct}'. "
            f"Must be one of: {sorted(VALID_CLAIM_TYPES)}"
        )

    # sources
    sources = claim.get("sources")
    if sources is None:
        errors.append(f"[{claim_id}] missing required field: sources")
    elif not isinstance(sources, list):
        errors.append(f"[{claim_id}] sources must be a list")
    else:
        for i, src in enumerate(sources):
            if not isinstance(src, dict):
                errors.append(f"[{claim_id}] sources[{i}] must be a dict")
                continue
            src_type = src.get("type")
            if src_type not in VALID_SOURCE_TYPES:
                errors.append(
                    f"[{claim_id}] sources[{i}].type '{src_type}' invalid. "
                    f"Must be one of: {sorted(VALID_SOURCE_TYPES)}"
                )
            if not src.get("reference"):
                errors.append(
                    f"[{claim_id}] sources[{i}].reference must be non-empty"
                )

        # Check source requirements for claim_type
        if ct in CLAIM_TYPE_SOURCE_REQUIREMENTS:
            req_types, req_min = CLAIM_TYPE_SOURCE_REQUIREMENTS[ct]
            if req_types and req_min > 0:
                matching = [
                    s for s in sources
                    if isinstance(s, dict) and s.get("type") in req_types
                ]
                if len(matching) < req_min:
                    errors.append(
                        f"[{claim_id}] claim_type '{ct}' requires at least "
                        f"{req_min} source(s) of type {sorted(req_types)}, "
                        f"found {len(matching)}"
                    )

    # confidence
    conf = claim.get("confidence")
    if conf is None:
        errors.append(f"[{claim_id}] missing required field: confidence")
    elif not isinstance(conf, (int, float)):
        errors.append(f"[{claim_id}] confidence must be a number")
    elif not (0 <= conf <= 100):
        errors.append(f"[{claim_id}] confidence must be 0-100, got {conf}")

    # uncertainty (optional — str or null)
    if "uncertainty" in claim:
        unc = claim["uncertainty"]
        if unc is not None and not isinstance(unc, str):
            errors.append(
                f"[{claim_id}] uncertainty must be a string or null"
            )

    return errors


def validate_claim_id_prefix(claim_id: str, agent_name: str) -> Optional[str]:
    """Validate that claim ID uses the correct prefix for the agent.

    Returns error message or None if valid.
    """
    expected = AGENT_CLAIM_PREFIXES.get(agent_name)
    if expected is None:
        return None  # Unknown agent — skip prefix check

    if not claim_id.startswith(expected + "-"):
        return (
            f"Claim '{claim_id}' should start with '{expected}-' "
            f"for agent '{agent_name}'"
        )
    return None


def validate_claims_batch(
    claims: list[dict[str, Any]],
    agent_name: Optional[str] = None,
) -> dict[str, Any]:
    """Validate a batch of GroundedClaims.

    Returns:
        {
            "valid": bool,
            "total": int,
            "errors": list[str],
            "claim_ids": list[str],
            "duplicate_ids": list[str],
        }
    """
    all_errors: list[str] = []
    claim_ids: list[str] = []
    seen_ids: set[str] = set()
    duplicate_ids: list[str] = []

    for i, claim in enumerate(claims):
        if not isinstance(claim, dict):
            all_errors.append(f"claims[{i}] is not a dict")
            continue

        # Schema validation
        errs = validate_grounded_claim(claim)
        all_errors.extend(errs)

        # Prefix validation
        cid = claim.get("id", "")
        if cid and agent_name:
            prefix_err = validate_claim_id_prefix(cid, agent_name)
            if prefix_err:
                all_errors.append(prefix_err)

        # Duplicate detection
        if cid:
            if cid in seen_ids:
                duplicate_ids.append(cid)
            seen_ids.add(cid)
            claim_ids.append(cid)

    if duplicate_ids:
        all_errors.append(
            f"Duplicate claim IDs: {duplicate_ids}"
        )

    return {
        "valid": len(all_errors) == 0,
        "total": len(claims),
        "errors": all_errors,
        "claim_ids": claim_ids,
        "duplicate_ids": duplicate_ids,
    }


# ===================================================================
# 3. HALLUCINATION FIREWALL
# ===================================================================

def check_hallucination_firewall(text: str) -> list[dict[str, Any]]:
    """Scan text for hallucination patterns.

    Returns list of findings:
        [{"level": "BLOCK"|"REQUIRE_SOURCE"|"SOFTEN"|"VERIFY",
          "pattern": str, "match": str, "position": int}]

    Reference: workflow.md:631-639
    """
    findings: list[dict[str, Any]] = []

    for pattern in _FIREWALL_BLOCK:
        for m in pattern.finditer(text):
            findings.append({
                "level": "BLOCK",
                "pattern": pattern.pattern,
                "match": m.group(),
                "position": m.start(),
            })

    for pattern in _FIREWALL_REQUIRE_SOURCE:
        for m in pattern.finditer(text):
            findings.append({
                "level": "REQUIRE_SOURCE",
                "pattern": pattern.pattern,
                "match": m.group(),
                "position": m.start(),
            })

    for pattern in _FIREWALL_SOFTEN:
        for m in pattern.finditer(text):
            findings.append({
                "level": "SOFTEN",
                "pattern": pattern.pattern,
                "match": m.group(),
                "position": m.start(),
            })

    for pattern in _FIREWALL_VERIFY:
        for m in pattern.finditer(text):
            findings.append({
                "level": "VERIFY",
                "pattern": pattern.pattern,
                "match": m.group(),
                "position": m.start(),
            })

    # Sort by position for readability
    findings.sort(key=lambda f: f["position"])
    return findings


def has_blocking_hallucination(text: str) -> bool:
    """Quick check: does text contain any BLOCK-level hallucination pattern?"""
    return any(p.search(text) for p in _FIREWALL_BLOCK)


# ===================================================================
# 4. SRCS SCORING
# ===================================================================

def calculate_srcs_score(
    claim_type: str,
    cs: float,
    gs: float,
    us: float,
    vs: float,
) -> Optional[dict[str, Any]]:
    """Calculate weighted SRCS score for a single claim.

    Args:
        claim_type: One of VALID_CLAIM_TYPES
        cs: Citation Score (0-100)
        gs: Grounding Score (0-100)
        us: Uncertainty Score (0-100)
        vs: Verifiability Score (0-100)

    Returns:
        {"weighted_score": float, "weights": dict, "raw": dict,
         "claim_type": str} or None if invalid claim_type
    """
    weights = SRCS_WEIGHTS.get(claim_type)
    if weights is None:
        return None

    raw = {"CS": cs, "GS": gs, "US": us, "VS": vs}
    weighted = (
        cs * weights["CS"]
        + gs * weights["GS"]
        + us * weights["US"]
        + vs * weights["VS"]
    )

    return {
        "weighted_score": round(weighted, 2),
        "weights": weights,
        "raw": raw,
        "claim_type": claim_type,
    }


def calculate_agent_srcs(
    claims_scores: list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate aggregate SRCS for an agent's claims.

    Args:
        claims_scores: List of results from calculate_srcs_score()

    Returns:
        {"average_score": float, "min_score": float, "max_score": float,
         "total_claims": int, "below_threshold": list[dict]}
    """
    if not claims_scores:
        return {
            "average_score": 0.0,
            "min_score": 0.0,
            "max_score": 0.0,
            "total_claims": 0,
            "below_threshold": [],
        }

    scores = [c["weighted_score"] for c in claims_scores if c is not None]
    if not scores:
        return {
            "average_score": 0.0,
            "min_score": 0.0,
            "max_score": 0.0,
            "total_claims": 0,
            "below_threshold": [],
        }

    # SRCS score threshold: claims below this are flagged (workflow.md:979)
    srcs_threshold = 70
    below: list[dict[str, Any]] = []
    for c in claims_scores:
        if c is None:
            continue
        ct = c.get("claim_type", "")
        if c["weighted_score"] < srcs_threshold:
            below.append({
                "claim_type": ct,
                "score": c["weighted_score"],
                "threshold": srcs_threshold,
            })

    return {
        "average_score": round(sum(scores) / len(scores), 2),
        "min_score": round(min(scores), 2),
        "max_score": round(max(scores), 2),
        "total_claims": len(scores),
        "below_threshold": below,
    }


def validate_sermon_sot_schema(sermon_state: dict[str, Any]) -> list[str]:
    """Validate sermon-specific fields in state.yaml.

    Complements _context_lib.py:validate_sot_schema() which handles
    the base workflow schema. This validates the `sermon:` namespace.

    Args:
        sermon_state: The `workflow.sermon` sub-dict from state.yaml

    Returns: list of warning strings (empty = valid)
    """
    warnings: list[str] = []
    if not sermon_state or not isinstance(sermon_state, dict):
        return warnings

    # SM-1: mode — must be one of INPUT_MODES
    mode = sermon_state.get("mode")
    if mode is not None and mode not in INPUT_MODES:
        warnings.append(
            f"sermon.mode '{mode}' invalid. Must be one of: {sorted(INPUT_MODES)}"
        )

    # SM-2: passage — must be non-empty string if present
    passage = sermon_state.get("passage")
    if passage is not None:
        if not isinstance(passage, str) or not passage.strip():
            warnings.append("sermon.passage must be a non-empty string")

    # SM-3: output_dir — must be non-empty string if present
    output_dir = sermon_state.get("output_dir")
    if output_dir is not None:
        if not isinstance(output_dir, str) or not output_dir.strip():
            warnings.append("sermon.output_dir must be a non-empty string")

    # SM-4: completed_gates — must be list of valid gate names
    gates = sermon_state.get("completed_gates")
    if gates is not None:
        valid_gates = set(WAVE_GATE_MAP.keys())
        if not isinstance(gates, list):
            warnings.append("sermon.completed_gates must be a list")
        else:
            for g in gates:
                if g not in valid_gates:
                    warnings.append(
                        f"sermon.completed_gates contains unknown gate '{g}'"
                    )

    # SM-5: srcs_threshold — must be number 0-100
    threshold = sermon_state.get("srcs_threshold")
    if threshold is not None:
        if not isinstance(threshold, (int, float)):
            warnings.append("sermon.srcs_threshold must be a number")
        elif not (0 <= threshold <= 100):
            warnings.append(
                f"sermon.srcs_threshold must be 0-100, got {threshold}"
            )

    return warnings


def validate_srcs_output(srcs_result: dict[str, Any]) -> list[str]:
    """Validate SRCS evaluation output structure.

    Returns list of errors. Empty = valid.
    """
    errors: list[str] = []

    required_keys = [
        "average_score", "min_score", "max_score",
        "total_claims", "below_threshold",
    ]
    for key in required_keys:
        if key not in srcs_result:
            errors.append(f"Missing required key: {key}")

    avg = srcs_result.get("average_score")
    if avg is not None and not isinstance(avg, (int, float)):
        errors.append("average_score must be a number")

    total = srcs_result.get("total_claims")
    if total is not None and (not isinstance(total, int) or total < 0):
        errors.append("total_claims must be a non-negative integer")

    below = srcs_result.get("below_threshold")
    if below is not None and not isinstance(below, list):
        errors.append("below_threshold must be a list")

    return errors


# ===================================================================
# 5. CROSS-VALIDATION GATE — Structural Validation
# ===================================================================

def validate_gate_structure(
    gate_name: str,
    output_dir: str,
) -> dict[str, Any]:
    """Validate structural requirements for a cross-validation gate.

    Checks:
      - All expected agent output files exist
      - Files are non-empty (> 100 bytes)
      - Files contain claims section

    This is the CODE part of the HYBRID gate.
    The AI part (semantic consistency) is Orchestrator's job.

    Returns:
        {"passed": bool, "gate": str, "checks": list[dict],
         "missing_files": list[str], "empty_files": list[str]}
    """
    agents = WAVE_GATE_MAP.get(gate_name, [])
    if not agents:
        return {
            "passed": False,
            "gate": gate_name,
            "checks": [],
            "missing_files": [],
            "empty_files": [],
            "error": f"Unknown gate: {gate_name}",
        }

    research_dir = os.path.join(output_dir, "research-package")
    checks: list[dict[str, Any]] = []
    missing: list[str] = []
    empty: list[str] = []

    for agent in agents:
        filename = AGENT_OUTPUT_FILES.get(agent, "")
        filepath = os.path.join(research_dir, filename)
        check: dict[str, Any] = {
            "agent": agent,
            "file": filename,
            "exists": False,
            "size_ok": False,
            "has_claims": False,
        }

        if not os.path.isfile(filepath):
            missing.append(filename)
        else:
            check["exists"] = True
            size = os.path.getsize(filepath)
            if size < 100:
                empty.append(filename)
            else:
                check["size_ok"] = True
                # Quick check for claims section
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read(5000)  # Read first 5KB
                    check["has_claims"] = bool(
                        re.search(r"^\s*claims:\s*$", content, re.MULTILINE)
                        or "- id:" in content
                    )
                except OSError:
                    pass

        checks.append(check)

    all_exist = len(missing) == 0
    all_sized = len(empty) == 0
    passed = all_exist and all_sized

    return {
        "passed": passed,
        "gate": gate_name,
        "checks": checks,
        "missing_files": missing,
        "empty_files": empty,
    }


def validate_gate_result(
    gate_name: str,
    structural_passed: bool,
    semantic_passed: bool,
    findings: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Record gate validation result for SOT.

    Returns dict suitable for state.yaml gate recording.
    """
    return {
        "gate": gate_name,
        "passed": structural_passed and semantic_passed,
        "structural_passed": structural_passed,
        "semantic_passed": semantic_passed,
        "findings": findings or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ===================================================================
# 6. CHECKLIST MANAGEMENT
# ===================================================================

def generate_checklist() -> str:
    """Generate the todo-checklist.md content (155 steps per workflow.md table).

    Reference: workflow.md:1078-1099
    """
    lines: list[str] = []
    lines.append("# Sermon Research Workflow Checklist")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")

    step_num = 1
    for section_name, count in CHECKLIST_SECTIONS:
        lines.append(f"## {section_name}")
        lines.append("")
        for i in range(count):
            lines.append(f"- [ ] Step {step_num}: {section_name} — Task {i + 1}")
            step_num += 1
        lines.append("")

    total = step_num - 1
    lines.append(f"---")
    lines.append(f"Total steps: {total}")
    lines.append(f"Completed: 0/{total}")
    return "\n".join(lines)


def update_checklist(filepath: str, step: int, completed: bool = True) -> bool:
    """Update a specific step's completion status in the checklist.

    Returns True if step was found and updated, False otherwise.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return False

    pattern = re.compile(
        rf"^- \[([ x])\] Step {step}:(.*)$",
        re.MULTILINE,
    )

    match = pattern.search(content)
    if not match:
        return False

    mark = "x" if completed else " "
    new_line = f"- [{mark}] Step {step}:{match.group(2)}"
    content = content[:match.start()] + new_line + content[match.end():]

    # Update completion count
    done = len(re.findall(r"^- \[x\]", content, re.MULTILINE))
    total_match = re.search(r"^Total steps: (\d+)", content, re.MULTILINE)
    total = int(total_match.group(1)) if total_match else 120
    content = re.sub(
        r"^Completed: \d+/\d+",
        f"Completed: {done}/{total}",
        content,
        flags=re.MULTILINE,
    )

    try:
        tmp = filepath + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, filepath)
        return True
    except OSError:
        return False


def get_checklist_progress(filepath: str) -> dict[str, Any]:
    """Parse checklist and return progress summary.

    Returns:
        {"total": int, "completed": int, "remaining": int,
         "percentage": float, "last_completed_step": int,
         "next_step": int, "section_progress": dict}
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return {
            "total": 0, "completed": 0, "remaining": 0,
            "percentage": 0.0, "last_completed_step": 0,
            "next_step": 1, "section_progress": {},
        }

    completed_steps: list[int] = []
    incomplete_steps: list[int] = []

    for m in re.finditer(r"^- \[([ x])\] Step (\d+):", content, re.MULTILINE):
        step_num = int(m.group(2))
        if m.group(1) == "x":
            completed_steps.append(step_num)
        else:
            incomplete_steps.append(step_num)

    total = len(completed_steps) + len(incomplete_steps)
    done = len(completed_steps)
    last = max(completed_steps) if completed_steps else 0
    nxt = min(incomplete_steps) if incomplete_steps else (total + 1)

    # Section progress
    section_progress: dict[str, dict[str, int]] = {}
    current_section = ""
    for line in content.split("\n"):
        if line.startswith("## "):
            current_section = line[3:].strip()
            section_progress[current_section] = {"total": 0, "completed": 0}
        elif line.startswith("- ["):
            if current_section in section_progress:
                section_progress[current_section]["total"] += 1
                if line.startswith("- [x]"):
                    section_progress[current_section]["completed"] += 1

    return {
        "total": total,
        "completed": done,
        "remaining": total - done,
        "percentage": round((done / total * 100) if total > 0 else 0, 1),
        "last_completed_step": last,
        "next_step": nxt,
        "section_progress": section_progress,
    }


# ===================================================================
# 7. SESSION INITIALIZATION (Phase 0)
# ===================================================================

def generate_session_json(
    mode: str,
    user_input: str,
    options: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Generate initial session.json content.

    Reference: workflow.md:56-61
    """
    if mode not in INPUT_MODES:
        mode = "theme"  # Safe default

    return {
        "version": "2.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "input": user_input,
        "options": options or {
            "analysis_level": "Standard",
            "research_scope": "full",
        },
        "context_snapshots": {},
        "translation_state": {
            "completed_phases": [],
            "glossary_terms_added": 0,
            "glossary_updated_at": None,
            "failed_translations": [],
        },
        "status": "initialized",
    }


def get_output_dir_name(title: str) -> str:
    """Generate output directory name from sermon title.

    Format: sermon-output/[title-YYYY-MM-DD]/

    Colons and slashes are converted to hyphens (e.g., "8:1-10" -> "8-1-10")
    before stripping remaining special characters.
    """
    safe_title = re.sub(r"[:/]", "-", title)  # colons/slashes -> hyphens
    safe_title = re.sub(r"[^\w\s가-힣-]", "", safe_title).strip()
    safe_title = re.sub(r"\s+", "-", safe_title)[:50]
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"sermon-output/{safe_title}-{date_str}"


def create_output_structure(base_dir: str) -> dict[str, str]:
    """Create the output directory structure with collision avoidance.

    If base_dir already exists (e.g., same passage on same day),
    appends a numeric suffix (-2, -3, ...) to avoid overwriting.

    Returns dict of created directory paths.
    Reference: workflow.md:706-730

    P1 Compliance: Deterministic filesystem check only. No AI judgment.
    """
    actual_dir = base_dir
    if os.path.exists(base_dir):
        counter = 2
        while os.path.exists(f"{base_dir}-{counter}"):
            counter += 1
        actual_dir = f"{base_dir}-{counter}"

    dirs = {
        "root": actual_dir,
        "research": os.path.join(actual_dir, "research-package"),
        "temp": os.path.join(actual_dir, "_temp"),
        "pacs_logs": os.path.join(actual_dir, "pacs-logs"),
    }

    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    return dirs


def initialize_sermon_output(
    user_input: str,
    mode: str,
    options: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """P1 Master: Phase 0 complete initialization.

    Single call performs ALL Phase 0 setup:
      1. get_output_dir_name(user_input) -> directory name
      2. create_output_structure(base_dir) -> directories (with collision avoidance)
      3. generate_session_json(mode, user_input, options) -> session.json write
      4. generate_checklist() -> todo-checklist.md write

    The Orchestrator calls this ONCE, then writes the returned
    state_yaml_sermon dict to state.yaml. No other Phase 0 calls needed.

    P1 Compliance: 100% deterministic. Zero AI judgment.
    SOT Compliance: Writes session.json + checklist (domain files).
                    Returns state_yaml_sermon for Orchestrator to write to state.yaml
                    (preserving single-writer rule).

    Args:
        user_input: Raw user input (passage, theme, or series description)
        mode: Detected input mode ("passage", "theme", or "series")
        options: Optional overrides for analysis_level / research_scope

    Returns:
        {
            "success": bool,
            "output_dir": str,           # Final subdirectory path (collision-safe)
            "session_path": str,         # session.json absolute path
            "checklist_path": str,       # todo-checklist.md absolute path
            "state_yaml_sermon": {       # Orchestrator writes this to state.yaml
                "mode": str,
                "output_dir": str,
                "completed_gates": [],
                "srcs_threshold": 70,
            },
            "dirs": dict,               # All created directory paths
            "error": str | None,
        }
    """
    result: dict[str, Any] = {
        "success": False,
        "output_dir": "",
        "session_path": "",
        "checklist_path": "",
        "state_yaml_sermon": {},
        "dirs": {},
        "error": None,
    }

    # Step 1: Generate directory name from user input
    base_dir = get_output_dir_name(user_input)

    # Step 2: Create directory structure (with collision avoidance)
    try:
        dirs = create_output_structure(base_dir)
    except OSError as e:
        result["error"] = f"Cannot create output directory: {e}"
        return result

    actual_dir = dirs["root"]
    result["output_dir"] = actual_dir
    result["dirs"] = dirs

    # Step 3: Generate and write session.json
    session_data = generate_session_json(mode, user_input, options)
    session_path = os.path.join(actual_dir, "session.json")
    try:
        tmp = session_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, session_path)
    except OSError as e:
        result["error"] = f"Cannot write session.json: {e}"
        return result
    result["session_path"] = session_path

    # Step 4: Generate and write todo-checklist.md
    checklist_content = generate_checklist()
    checklist_path = os.path.join(actual_dir, "todo-checklist.md")
    try:
        tmp = checklist_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(checklist_content)
        os.replace(tmp, checklist_path)
    except OSError as e:
        result["error"] = f"Cannot write checklist: {e}"
        return result
    result["checklist_path"] = checklist_path

    # Step 5: Build state.yaml sermon section values
    result["state_yaml_sermon"] = {
        "mode": mode if mode in INPUT_MODES else "theme",
        "output_dir": actual_dir,
        "completed_gates": [],
        "srcs_threshold": 70,
    }

    result["success"] = True
    return result


def detect_input_mode(user_input: str) -> str:
    """Detect input mode from user input string.

    Reference: workflow.md:92-97
    Returns: "theme", "passage", or "series"
    """
    # Passage patterns: book chapter:verse
    passage_patterns = [
        re.compile(r"\b\d+:\d+"),  # N:N (chapter:verse)
        re.compile(r"(Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|"
                   r"Judges|Ruth|Samuel|Kings|Chronicles|Ezra|Nehemiah|"
                   r"Esther|Job|Psalms?|Proverbs?|Ecclesiastes|Song|"
                   r"Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|"
                   r"Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|"
                   r"Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|"
                   r"Luke|John|Acts|Romans|Corinthians|Galatians|"
                   r"Ephesians|Philippians|Colossians|Thessalonians|"
                   r"Timothy|Titus|Philemon|Hebrews|James|Peter|"
                   r"Jude|Revelation)", re.IGNORECASE),
        # Korean book names
        re.compile(r"(창세기|출애굽기|레위기|민수기|신명기|여호수아|사사기|"
                   r"룻기|사무엘|열왕기|역대|에스라|느헤미야|에스더|욥기|"
                   r"시편|잠언|전도서|아가|이사야|예레미야|예레미야애가|"
                   r"에스겔|다니엘|호세아|요엘|아모스|오바댜|요나|미가|"
                   r"나훔|하박국|스바냐|학개|스가랴|말라기|마태복음|"
                   r"마가복음|누가복음|요한복음|사도행전|로마서|"
                   r"고린도전서|고린도후서|갈라디아서|에베소서|빌립보서|"
                   r"골로새서|데살로니가전서|데살로니가후서|디모데전서|"
                   r"디모데후서|디도서|빌레몬서|히브리서|야고보서|"
                   r"베드로전서|베드로후서|요한1서|요한2서|요한3서|"
                   r"유다서|요한계시록)"),
    ]

    # Series patterns
    series_patterns = [
        re.compile(r"시리즈|series|연속|주차|week\s*\d+", re.IGNORECASE),
    ]

    # Check series first (more specific)
    for p in series_patterns:
        if p.search(user_input):
            return "series"

    # Check passage
    for p in passage_patterns:
        if p.search(user_input):
            return "passage"

    # Default to theme
    return "theme"


# ===================================================================
# 8. ERROR HANDLING — 5 Failure Types
# ===================================================================

_FAILURE_PATTERNS: dict[str, re.Pattern[str]] = {
    "LOOP_EXHAUSTED": re.compile(
        r"\[FAILURE:LOOP_EXHAUSTED\]|\bLOOP_EXHAUSTED\b",
        re.IGNORECASE,
    ),
    "SOURCE_UNAVAILABLE": re.compile(
        r"\[FAILURE:SOURCE_UNAVAILABLE\]|\bSOURCE_UNAVAILABLE\b",
        re.IGNORECASE,
    ),
    "INPUT_INVALID": re.compile(
        r"\[FAILURE:INPUT_INVALID\]|\bINPUT_INVALID\b",
        re.IGNORECASE,
    ),
    "CONFLICT_UNRESOLVABLE": re.compile(
        r"\[FAILURE:CONFLICT_UNRESOLVABLE\]|\bCONFLICT_UNRESOLVABLE\b",
        re.IGNORECASE,
    ),
    "OUT_OF_SCOPE": re.compile(
        r"\[FAILURE:OUT_OF_SCOPE\]|\bOUT_OF_SCOPE\b",
        re.IGNORECASE,
    ),
}

# Failure type → handler configuration (workflow.md:1012-1040)
FAILURE_HANDLERS: dict[str, dict[str, Any]] = {
    "LOOP_EXHAUSTED": {
        "action": "return_partial",
        "notify": True,
        "message": "Agent exhausted thought loops (max 3). Partial results available.",
    },
    "SOURCE_UNAVAILABLE": {
        "action": "seek_alternative",
        "fallback": "skip_with_note",
        "notify": True,
        "message": "Required source unavailable. Seeking alternatives.",
    },
    "INPUT_INVALID": {
        "action": "request_retry",
        "notify": True,
        "message": "Invalid input detected. Please re-enter.",
    },
    "CONFLICT_UNRESOLVABLE": {
        "action": "present_both_views",
        "notify": True,
        "message": "Unresolvable conflict. Both views will be presented.",
    },
    "OUT_OF_SCOPE": {
        "action": "return_in_scope_only",
        "notify": True,
        "message": "Out-of-scope content detected. Returning in-scope results only.",
    },
}


def parse_agent_failure(output: str) -> Optional[str]:
    """Detect failure type from agent output text.

    Returns failure type string or None if no failure detected.
    """
    for ftype, pattern in _FAILURE_PATTERNS.items():
        if pattern.search(output):
            return ftype
    return None


def get_failure_handler(failure_type: str) -> Optional[dict[str, Any]]:
    """Get handler configuration for a failure type.

    Returns handler dict or None if unknown failure type.
    """
    return FAILURE_HANDLERS.get(failure_type)


# --- Workflow-level error handlers (workflow.md:1029-1040) ---

def handle_research_incomplete(
    completed_agents: list[str],
    expected_agents: list[str],
) -> dict[str, Any]:
    """Handle on_research_incomplete: some agents did not produce output.

    Reference: workflow.md:1029-1032 (action: partial_proceed)
    Returns action descriptor for the Orchestrator.
    """
    missing = [a for a in expected_agents if a not in completed_agents]
    return {
        "action": "partial_proceed",
        "notify": True,
        "missing_agents": missing,
        "completed_count": len(completed_agents),
        "expected_count": len(expected_agents),
        "message": (
            f"{len(missing)}개 에이전트 분석이 불완전합니다: "
            f"{', '.join(missing)}. 계속 진행하시겠습니까?"
        ),
    }


def handle_validation_failure(
    gate_name: str,
    structural_passed: bool,
    semantic_passed: bool,
    findings: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Handle on_validation_failure: gate validation failed.

    Reference: workflow.md:1034-1035 (action: request_human_review)
    Returns action descriptor for the Orchestrator.
    """
    failure_reasons = []
    if not structural_passed:
        failure_reasons.append("structural check failed")
    if not semantic_passed:
        failure_reasons.append("semantic consistency check failed")

    return {
        "action": "request_human_review",
        "gate": gate_name,
        "structural_passed": structural_passed,
        "semantic_passed": semantic_passed,
        "failure_reasons": failure_reasons,
        "findings": findings or [],
        "message": (
            f"{gate_name} 검증 실패: {', '.join(failure_reasons)}. "
            f"사람의 검토가 필요합니다."
        ),
    }


def handle_srcs_below_threshold(
    agent_results: dict[str, dict[str, Any]],
    threshold: float = 70.0,
) -> dict[str, Any]:
    """Handle on_srcs_below_threshold: SRCS scores below minimum.

    Reference: workflow.md:1037-1039 (action: flag_for_review, threshold: 70)
    Returns action descriptor with flagged agents/claims.
    """
    flagged_agents: list[dict[str, Any]] = []
    for agent, result in agent_results.items():
        avg = result.get("average_score", 0)
        if avg < threshold:
            flagged_agents.append({
                "agent": agent,
                "average_score": avg,
                "below_threshold_claims": result.get("below_threshold", []),
            })

    return {
        "action": "flag_for_review",
        "threshold": threshold,
        "flagged_count": len(flagged_agents),
        "flagged_agents": flagged_agents,
        "requires_review": len(flagged_agents) > 0,
        "message": (
            f"{len(flagged_agents)}개 에이전트의 SRCS 점수가 "
            f"기준({threshold}) 미만입니다."
        ) if flagged_agents else "모든 에이전트 SRCS 점수 기준 충족.",
    }


# ===================================================================
# 9. WAVE BOUNDARY DETECTION
# ===================================================================

def get_current_wave(step: int) -> Optional[str]:
    """Determine which wave a step number belongs to.

    Based on CHECKLIST_SECTIONS step ranges.
    """
    current = 1
    for section_name, count in CHECKLIST_SECTIONS:
        end = current + count - 1
        if current <= step <= end:
            if section_name.startswith("Wave 1"):
                return "wave-1"
            elif section_name.startswith("Wave 2"):
                return "wave-2"
            elif section_name.startswith("Wave 3"):
                return "wave-3"
            elif section_name.startswith("Wave 4"):
                return "wave-4"
            else:
                return section_name
        current = end + 1
    return None


def check_pending_gate(current_step: int, completed_gates: list[str]) -> Optional[str]:
    """Check if there's an unexecuted gate before the current step.

    Returns gate name if a gate is pending, None otherwise.
    Gates fire at wave boundaries (end of Wave 1/2/3 sections).
    """
    # Compute wave end steps from CHECKLIST_SECTIONS
    # Match only analysis sections, not translation sections
    step = 1
    wave_end_steps: dict[str, int] = {}
    for section_name, count in CHECKLIST_SECTIONS:
        end = step + count - 1
        if section_name.startswith("Wave 1:"):
            wave_end_steps["gate-1"] = end
        elif section_name.startswith("Wave 2:"):
            wave_end_steps["gate-2"] = end
        elif section_name.startswith("Wave 3:"):
            wave_end_steps["gate-3"] = end
        step = end + 1

    for gate_name, wave_end in wave_end_steps.items():
        if current_step > wave_end and gate_name not in completed_gates:
            return gate_name

    return None


# ===================================================================
# 10. UTILITY FUNCTIONS
# ===================================================================

def confidence_check(claim_type: str, confidence: float) -> dict[str, Any]:
    """Check if confidence meets threshold for claim type.

    Returns: {"meets_threshold": bool, "threshold": int,
              "confidence": float, "claim_type": str}
    """
    threshold = CONFIDENCE_THRESHOLDS.get(claim_type, 70)
    return {
        "meets_threshold": confidence >= threshold,
        "threshold": threshold,
        "confidence": confidence,
        "claim_type": claim_type,
    }


def format_srcs_report(agent_results: dict[str, dict[str, Any]]) -> str:
    """Format SRCS results into a markdown report.

    Args:
        agent_results: {agent_name: calculate_agent_srcs() result}
    """
    lines: list[str] = []
    lines.append("# SRCS Evaluation Summary")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")

    # Overall statistics
    all_scores = [
        r["average_score"] for r in agent_results.values()
        if r.get("total_claims", 0) > 0
    ]
    if all_scores:
        overall_avg = round(sum(all_scores) / len(all_scores), 2)
        lines.append(f"## Overall: {overall_avg}/100")
    else:
        lines.append("## Overall: N/A (no claims)")
    lines.append("")

    # Per-agent table
    lines.append("| Agent | Avg Score | Claims | Below Threshold |")
    lines.append("|-------|-----------|--------|-----------------|")
    for agent, result in sorted(agent_results.items()):
        avg = result.get("average_score", 0)
        total = result.get("total_claims", 0)
        below = len(result.get("below_threshold", []))
        lines.append(f"| {agent} | {avg} | {total} | {below} |")

    lines.append("")

    # Flag agents below threshold
    flagged = [
        (agent, result)
        for agent, result in agent_results.items()
        if result.get("below_threshold")
    ]
    if flagged:
        lines.append("## Claims Below Threshold")
        lines.append("")
        for agent, result in flagged:
            for item in result["below_threshold"]:
                lines.append(
                    f"- **{agent}**: {item['claim_type']} "
                    f"score {item['score']} < threshold {item['threshold']}"
                )
        lines.append("")

    return "\n".join(lines)


# ===================================================================
# 11. AGENT DISPATCH — Dependency Resolution & Prompt Generation
# ===================================================================

def resolve_dependency_files(
    agent_name: str,
    output_dir: str,
) -> list[dict[str, str]]:
    """Resolve dependency file paths for a research agent.

    Returns list of {"agent": str, "path": str} for each dependency.
    Empty list for Wave 1 agents (no dependencies).

    Reference: workflow.md:765-808 (depends_on fields)
    """
    deps = AGENT_DEPENDENCIES.get(agent_name, [])
    result: list[dict[str, str]] = []
    for dep_agent in deps:
        dep_file = AGENT_OUTPUT_FILES.get(dep_agent)
        if dep_file:
            dep_path = os.path.join(output_dir, "research-package", dep_file)
            result.append({"agent": dep_agent, "path": dep_path})
    return result


def build_research_agent_prompt(
    agent_name: str,
    passage: str,
    output_dir: str,
    analysis_level: str = "Standard",
) -> Optional[str]:
    """Generate deterministic runtime prompt for a GRA research agent.

    The agent's static instructions are loaded from .claude/agents/{agent}.md
    via Claude Code's subagent_type mechanism. This function generates
    only the runtime parameters that vary per execution.

    Args:
        agent_name: Must be one of the 11 GRA research agents
        passage: Bible passage text (e.g., "Psalm 23:1-6")
        output_dir: Base output directory
        analysis_level: "Standard", "Advanced", or "Expert"

    Returns:
        Formatted prompt string, or None if agent_name is not a research agent

    Reference: workflow.md:202-343 (agent definitions)
    """
    output_file = AGENT_OUTPUT_FILES.get(agent_name)
    if output_file is None:
        return None  # Not a research agent

    output_path = os.path.join(output_dir, "research-package", output_file)

    lines = [
        "## Runtime Parameters",
        "",
        f"Passage: {passage}",
        f"Analysis Level: {analysis_level}",
        f"Output File: {output_path}",
        "",
        "## Required Reading",
        "Read `.claude/agents/references/gra-compliance.md` before starting.",
        "All claims must conform to the GroundedClaim schema defined therein.",
    ]

    # Add dependency files for Wave 2+ agents
    deps = resolve_dependency_files(agent_name, output_dir)
    if deps:
        lines.append("")
        lines.append("## Dependency Files (read before starting your analysis)")
        for dep in deps:
            lines.append(f"- {dep['agent']}: `{dep['path']}`")

    return "\n".join(lines)


# ===================================================================
# 12. AGENT OUTPUT VALIDATION — P1 Deterministic Pipeline
# ===================================================================

def extract_claims_from_output(
    filepath: str,
) -> dict[str, Any]:
    """Extract and parse YAML claims from an agent's markdown output.

    Deterministically finds ```yaml blocks containing 'claims:' key,
    parses them with PyYAML, and returns structured data.

    P1 Compliance: No AI judgment. Pure regex + YAML parsing.

    Returns:
        {
            "success": bool,
            "claims": list[dict],
            "raw_yaml": str,
            "error": str | None,
        }
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        return {
            "success": False, "claims": [], "raw_yaml": "",
            "error": f"Cannot read file: {e}",
        }

    # Find YAML code blocks
    yaml_blocks = re.findall(
        r"```ya?ml\s*\n(.*?)```",
        content,
        re.DOTALL,
    )

    if not yaml_blocks:
        # Fallback: unfenced claims: section
        claims_match = re.search(
            r"^(claims:\s*\n(?:\s+.*\n?)+)",
            content,
            re.MULTILINE,
        )
        if claims_match:
            yaml_blocks = [claims_match.group(1)]

    if not yaml_blocks:
        return {
            "success": False, "claims": [], "raw_yaml": "",
            "error": "No YAML claims block found in output",
        }

    # Parse YAML blocks
    try:
        import yaml
    except ImportError:
        return {
            "success": False, "claims": [], "raw_yaml": "",
            "error": "PyYAML not installed. Run: pip install pyyaml",
        }

    all_claims: list[dict[str, Any]] = []
    raw_parts: list[str] = []

    for block in yaml_blocks:
        raw_parts.append(block)
        try:
            parsed = yaml.safe_load(block)
        except yaml.YAMLError:
            continue  # Skip malformed blocks

        if isinstance(parsed, dict) and "claims" in parsed:
            claims_data = parsed["claims"]
            if isinstance(claims_data, list):
                all_claims.extend(claims_data)

    raw_yaml = "\n---\n".join(raw_parts)

    if not all_claims:
        return {
            "success": False, "claims": [], "raw_yaml": raw_yaml,
            "error": "YAML blocks found but no valid 'claims' key with list value",
        }

    return {
        "success": True, "claims": all_claims,
        "raw_yaml": raw_yaml, "error": None,
    }


def validate_agent_output(
    filepath: str,
    agent_name: str,
) -> dict[str, Any]:
    """All-in-one validation pipeline for a research agent's output.

    Combines L0 validation, claim extraction, schema validation,
    and hallucination firewall into a single deterministic pipeline.

    P1 Compliance: The Orchestrator calls this ONE function after each
    agent completes. No AI judgment needed for validation.

    Returns:
        {
            "valid": bool,
            "agent": str,
            "filepath": str,
            "l0": {"exists": bool, "size_ok": bool, "size": int},
            "claims": {"extracted": int, "valid": bool,
                       "errors": list[str], "claim_ids": list[str]},
            "firewall": {"block_count": int, "findings": list[dict]},
            "errors": list[str],
        }
    """
    result: dict[str, Any] = {
        "valid": True,
        "agent": agent_name,
        "filepath": filepath,
        "l0": {"exists": False, "size_ok": False, "size": 0},
        "claims": {"extracted": 0, "valid": True, "errors": [], "claim_ids": []},
        "firewall": {"block_count": 0, "findings": []},
        "errors": [],
    }

    # --- L0: File existence and size ---
    if not os.path.isfile(filepath):
        result["valid"] = False
        result["errors"].append(f"Output file not found: {filepath}")
        return result

    result["l0"]["exists"] = True
    size = os.path.getsize(filepath)
    result["l0"]["size"] = size

    if size < 100:
        result["valid"] = False
        result["l0"]["size_ok"] = False
        result["errors"].append(f"Output file too small: {size} bytes (min 100)")
        return result

    result["l0"]["size_ok"] = True

    # --- Read file content ---
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        result["valid"] = False
        result["errors"].append(f"Cannot read file: {e}")
        return result

    # --- Hallucination Firewall ---
    firewall_findings = check_hallucination_firewall(content)
    block_findings = [f for f in firewall_findings if f["level"] == "BLOCK"]
    result["firewall"]["findings"] = firewall_findings
    result["firewall"]["block_count"] = len(block_findings)

    if block_findings:
        result["valid"] = False
        for bf in block_findings:
            result["errors"].append(
                f"BLOCK-level hallucination: '{bf['match']}' "
                f"at position {bf['position']}"
            )

    # --- Claim Extraction & Validation (GRA agents only) ---
    if agent_name in AGENT_OUTPUT_FILES:
        extraction = extract_claims_from_output(filepath)

        if not extraction["success"]:
            result["valid"] = False
            result["errors"].append(
                f"Claim extraction failed: {extraction['error']}"
            )
        else:
            claims = extraction["claims"]
            result["claims"]["extracted"] = len(claims)

            validation = validate_claims_batch(claims, agent_name)
            result["claims"]["valid"] = validation["valid"]
            result["claims"]["errors"] = validation["errors"]
            result["claims"]["claim_ids"] = validation["claim_ids"]

            if not validation["valid"]:
                result["valid"] = False
                result["errors"].extend(validation["errors"])

    return result


# ===================================================================
# 13. GATE COMPLETION — Safe SOT Update
# ===================================================================

def record_gate_completion(
    sermon_state: dict[str, Any],
    gate_name: str,
) -> dict[str, Any]:
    """Safely record gate completion in sermon state.

    Validates gate name, prevents duplicates, ensures ordering.
    Returns result dict; does NOT write to file (Orchestrator's job).

    Returns:
        {"success": bool, "sermon_state": dict, "error": str | None}
    """
    valid_gates = set(WAVE_GATE_MAP.keys())

    if gate_name not in valid_gates:
        return {
            "success": False,
            "sermon_state": sermon_state,
            "error": f"Invalid gate name '{gate_name}'. "
                     f"Valid: {sorted(valid_gates)}",
        }

    completed = sermon_state.get("completed_gates", [])
    if not isinstance(completed, list):
        completed = []

    if gate_name in completed:
        return {
            "success": False,
            "sermon_state": sermon_state,
            "error": f"Gate '{gate_name}' already recorded as completed",
        }

    # Validate ordering: gate-1 before gate-2 before gate-3
    gate_order = ["gate-1", "gate-2", "gate-3"]
    gate_idx = gate_order.index(gate_name) if gate_name in gate_order else -1

    if gate_idx > 0:
        required_prev = gate_order[gate_idx - 1]
        if required_prev not in completed:
            return {
                "success": False,
                "sermon_state": sermon_state,
                "error": (
                    f"Cannot complete '{gate_name}' before "
                    f"'{required_prev}'. Completed: {completed}"
                ),
            }

    updated = dict(sermon_state)
    updated["completed_gates"] = completed + [gate_name]

    return {
        "success": True,
        "sermon_state": updated,
        "error": None,
    }


# ===================================================================
# 14. TRANSLATION MANAGEMENT — P1 Deterministic Pipeline
# ===================================================================

# Translation pACS thresholds
_TRANSLATION_PACS_GREEN = 70
_TRANSLATION_PACS_YELLOW = 50

# Regex patterns for pACS score extraction from translator output
_PACS_SCORE_PATTERN = re.compile(
    r"\|\s*(?:Ft|Ct|Nt|Tt)\s*\([^)]*\)\s*\|\s*(\d{1,3})\s*\|",
)
_PACS_DIMENSION_PATTERN = re.compile(
    r"\|\s*(Ft|Ct|Nt|Tt)\s*\([^)]*\)\s*\|\s*(\d{1,3})\s*\|",
)

# Heading pattern for structural comparison
_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+", re.MULTILINE)

# Code block pattern for preservation check
_CODE_BLOCK_PATTERN = re.compile(r"^```\w*\s*$", re.MULTILINE)

# Discovered Terms section pattern
_DISCOVERED_TERMS_PATTERN = re.compile(
    r"^## Discovered Terms\s*\n(.*)",
    re.MULTILINE | re.DOTALL,
)
_DISCOVERED_TERM_ENTRY = re.compile(
    r'-\s+english:\s*"([^"]+)"\s*\n\s+korean:\s*"([^"]+)"',
)


def get_translation_targets(
    phase: str,
    output_dir: str,
) -> list[dict[str, str]]:
    """Return translation target files for a given phase/wave.

    P1 Compliance: Deterministic routing — no AI judgment about
    which files to translate. Fixed mapping from TRANSLATION_TARGETS.

    Args:
        phase: Key from TRANSLATION_TARGETS (e.g., "wave-1", "phase-2-message")
        output_dir: Base output directory (e.g., "sermon-output/trust-2026-03-06")

    Returns:
        List of {"source": str, "target": str} with absolute paths.
        Empty list if phase is not in TRANSLATION_TARGETS.
    """
    files = TRANSLATION_TARGETS.get(phase, [])
    result: list[dict[str, str]] = []

    # Files that live in research-package/ but are not in AGENT_OUTPUT_FILES
    _extra_research_files = {"confidence-report.md", "srcs-summary.json"}

    for filename in files:
        # Determine subdirectory: research files go in research-package/
        in_research = (
            filename in AGENT_OUTPUT_FILES.values()
            or filename in _extra_research_files
        )
        if in_research:
            source = os.path.join(output_dir, "research-package", filename)
        else:
            source = os.path.join(output_dir, filename)

        # .ko.md naming: insert .ko before .md
        base, ext = os.path.splitext(filename)
        ko_filename = f"{base}.ko{ext}"

        if in_research:
            target = os.path.join(output_dir, "research-package", ko_filename)
        else:
            target = os.path.join(output_dir, ko_filename)

        result.append({"source": source, "target": target})

    return result


def build_translation_prompt(
    source_file: str,
    glossary_path: str,
    output_dir: str,
) -> str:
    """Generate deterministic runtime prompt for @sermon-translator.

    Parallels build_research_agent_prompt() for research agents.
    The agent's static instructions are loaded from
    .claude/agents/sermon-translator.md via Claude Code's subagent_type.
    This function generates only runtime parameters.

    P1 Compliance: Orchestrator MUST use this function instead of
    manually constructing translation prompts.

    Args:
        source_file: Absolute path to English source .md file
        glossary_path: Path to theological-glossary.yaml
        output_dir: Base output directory for pACS log

    Returns:
        Formatted prompt string for Task(subagent_type="sermon-translator")
    """
    # Determine output path (.ko.md)
    source_dir = os.path.dirname(source_file)
    source_name = os.path.basename(source_file)
    base, ext = os.path.splitext(source_name)
    ko_filename = f"{base}.ko{ext}"
    target_file = os.path.join(source_dir, ko_filename)

    # pACS log path
    pacs_log = os.path.join(output_dir, "pacs-logs",
                            f"translation-pacs-{base}.md")

    lines = [
        "## Runtime Parameters",
        "",
        f"Source File: `{source_file}`",
        f"Output File: `{target_file}`",
        f"Glossary: `{glossary_path}`",
        f"pACS Log: `{pacs_log}`",
        "",
        "## Instructions",
        "1. Read the glossary file first.",
        "2. Read the source file completely.",
        "3. Translate following your protocol (Steps 1-7).",
        "4. Write the translation to the Output File path above.",
        "5. Write the pACS log to the pACS Log path above.",
    ]

    return "\n".join(lines)


def validate_translation_output(
    source_path: str,
    translation_path: str,
) -> dict[str, Any]:
    """Structural validation of translation against English source.

    P1 Compliance: Deterministic structural comparison using regex
    and string operations. No AI judgment — only mathematical checks.

    Validates:
    - L0: File existence and minimum size
    - Heading count match (h1-h6 between source and translation)
    - Code block preservation (code blocks not translated)
    - Size ratio within acceptable range (0.3-2.5)

    Args:
        source_path: Path to English original .md file
        translation_path: Path to Korean translation .ko.md file

    Returns:
        {
            "valid": bool,
            "source": str,
            "translation": str,
            "l0": {"exists": bool, "size_ok": bool, "size": int},
            "structure": {
                "heading_match": bool,
                "source_headings": int,
                "translation_headings": int,
                "code_blocks_preserved": bool,
                "source_code_blocks": int,
                "translation_code_blocks": int,
            },
            "size_ratio": float,
            "errors": list[str],
        }
    """
    result: dict[str, Any] = {
        "valid": True,
        "source": source_path,
        "translation": translation_path,
        "l0": {"exists": False, "size_ok": False, "size": 0},
        "structure": {
            "heading_match": True,
            "source_headings": 0,
            "translation_headings": 0,
            "code_blocks_preserved": True,
            "source_code_blocks": 0,
            "translation_code_blocks": 0,
        },
        "size_ratio": 0.0,
        "errors": [],
    }

    # --- L0: File existence and size ---
    if not os.path.isfile(translation_path):
        result["valid"] = False
        result["errors"].append(
            f"Translation file not found: {translation_path}")
        return result

    result["l0"]["exists"] = True
    size = os.path.getsize(translation_path)
    result["l0"]["size"] = size

    if size < 100:
        result["valid"] = False
        result["l0"]["size_ok"] = False
        result["errors"].append(
            f"Translation file too small: {size} bytes (min 100)")
        return result

    result["l0"]["size_ok"] = True

    # --- Read both files ---
    try:
        with open(source_path, "r", encoding="utf-8") as f:
            source_content = f.read()
        with open(translation_path, "r", encoding="utf-8") as f:
            translation_content = f.read()
    except OSError as e:
        result["valid"] = False
        result["errors"].append(f"Cannot read file: {e}")
        return result

    # --- Heading count comparison ---
    source_headings = _HEADING_PATTERN.findall(source_content)
    # Exclude headings from Discovered Terms section in translation
    trans_main = _DISCOVERED_TERMS_PATTERN.split(translation_content)[0]
    translation_headings = _HEADING_PATTERN.findall(trans_main)

    result["structure"]["source_headings"] = len(source_headings)
    result["structure"]["translation_headings"] = len(translation_headings)

    if len(source_headings) != len(translation_headings):
        result["structure"]["heading_match"] = False
        result["errors"].append(
            f"Heading count mismatch: source={len(source_headings)}, "
            f"translation={len(translation_headings)}"
        )
        # Heading mismatch is a warning, not a failure
        # (translator may split/merge minor headings)

    # --- Code block preservation ---
    source_blocks = _CODE_BLOCK_PATTERN.findall(source_content)
    translation_blocks = _CODE_BLOCK_PATTERN.findall(trans_main)

    result["structure"]["source_code_blocks"] = len(source_blocks)
    result["structure"]["translation_code_blocks"] = len(translation_blocks)

    if len(source_blocks) != len(translation_blocks):
        result["structure"]["code_blocks_preserved"] = False
        result["errors"].append(
            f"Code block count mismatch: source={len(source_blocks)}, "
            f"translation={len(translation_blocks)}"
        )

    # --- Size ratio ---
    source_size = len(source_content.encode("utf-8"))
    trans_size = len(translation_content.encode("utf-8"))

    if source_size > 0:
        ratio = trans_size / source_size
        result["size_ratio"] = round(ratio, 2)

        if ratio < 0.3 or ratio > 2.5:
            result["valid"] = False
            result["errors"].append(
                f"Size ratio out of range: {ratio:.2f} "
                f"(expected 0.3-2.5, source={source_size}B, "
                f"translation={trans_size}B)"
            )

    return result


def extract_translation_pacs(
    content: str,
) -> dict[str, Any]:
    """Extract pACS scores from @sermon-translator output.

    P1 Compliance: Regex-based score extraction + mathematical min()
    calculation. No AI judgment in grade determination.

    Parses the markdown table format:
    | Ft (Fidelity) | 85 | ... |
    | Ct (Completeness) | 90 | ... |
    | Nt (Naturalness) | 80 | ... |
    | Tt (Theological Accuracy) | 88 | ... |

    Args:
        content: Full text content of the translation output or pACS log

    Returns:
        {
            "success": bool,
            "scores": {"Ft": int, "Ct": int, "Nt": int, "Tt": int},
            "pacs": int,
            "grade": str,  # "GREEN" | "YELLOW" | "RED"
            "weak_dimension": str,  # lowest scoring dimension
            "error": str | None,
        }
    """
    result: dict[str, Any] = {
        "success": False,
        "scores": {"Ft": 0, "Ct": 0, "Nt": 0, "Tt": 0},
        "pacs": 0,
        "grade": "RED",
        "weak_dimension": "",
        "error": None,
    }

    matches = _PACS_DIMENSION_PATTERN.findall(content)
    if not matches:
        result["error"] = "No pACS scores found in content"
        return result

    found_dims: dict[str, int] = {}
    for dim, score_str in matches:
        try:
            score = int(score_str)
            if 0 <= score <= 100:
                found_dims[dim] = score
        except ValueError:
            continue

    required_min = {"Ft", "Ct", "Nt"}
    missing_min = required_min - set(found_dims.keys())
    if missing_min:
        result["error"] = f"Missing pACS dimensions: {sorted(missing_min)}"
        return result

    result["scores"] = {
        "Ft": found_dims["Ft"],
        "Ct": found_dims["Ct"],
        "Nt": found_dims["Nt"],
        "Tt": found_dims.get("Tt", 0),
    }

    pacs = min(found_dims.values())
    result["pacs"] = pacs

    # Find weakest dimension
    weak_dim = min(found_dims, key=found_dims.get)  # type: ignore[arg-type]
    result["weak_dimension"] = weak_dim

    # Grade determination (deterministic thresholds)
    if pacs >= _TRANSLATION_PACS_GREEN:
        result["grade"] = "GREEN"
    elif pacs >= _TRANSLATION_PACS_YELLOW:
        result["grade"] = "YELLOW"
    else:
        result["grade"] = "RED"

    result["success"] = True
    return result


def should_retranslate(
    pacs_result: dict[str, Any],
    retry_count: int,
    max_retries: int = 2,
) -> dict[str, Any]:
    """Determine if retranslation is needed based on pACS score.

    P1 Compliance: Numeric comparison only. No subjective judgment.

    Args:
        pacs_result: Output from extract_translation_pacs()
        retry_count: How many times this file has been retranslated
        max_retries: Maximum retranslation attempts (default 2)

    Returns:
        {
            "retranslate": bool,
            "reason": str,
            "retry_count": int,
            "max_retries": int,
        }
    """
    if not pacs_result.get("success"):
        return {
            "retranslate": True,
            "reason": f"pACS extraction failed: {pacs_result.get('error')}",
            "retry_count": retry_count,
            "max_retries": max_retries,
        }

    grade = pacs_result.get("grade", "RED")

    if grade == "GREEN":
        return {
            "retranslate": False,
            "reason": f"pACS GREEN ({pacs_result['pacs']})",
            "retry_count": retry_count,
            "max_retries": max_retries,
        }

    if grade == "YELLOW":
        return {
            "retranslate": False,
            "reason": (
                f"pACS YELLOW ({pacs_result['pacs']}), "
                f"weak: {pacs_result['weak_dimension']} — accepted with flag"
            ),
            "retry_count": retry_count,
            "max_retries": max_retries,
        }

    # RED
    if retry_count >= max_retries:
        return {
            "retranslate": False,
            "reason": (
                f"pACS RED ({pacs_result['pacs']}) but max retries "
                f"({max_retries}) exhausted — accepting with warning"
            ),
            "retry_count": retry_count,
            "max_retries": max_retries,
        }

    return {
        "retranslate": True,
        "reason": (
            f"pACS RED ({pacs_result['pacs']}), "
            f"weak: {pacs_result['weak_dimension']} — "
            f"retry {retry_count + 1}/{max_retries}"
        ),
        "retry_count": retry_count,
        "max_retries": max_retries,
    }


def collect_discovered_terms(
    translation_files: list[str],
) -> list[dict[str, str]]:
    """Aggregate Discovered Terms from multiple translation outputs.

    P1 Compliance: Pure regex parsing + deduplication. No AI judgment.

    Parses ## Discovered Terms YAML sections from .ko.md files.
    Deduplicates by English key (keeps first occurrence).

    Args:
        translation_files: List of .ko.md file paths

    Returns:
        List of {"english": str, "korean": str}. Empty if no new terms.
    """
    seen: set[str] = set()
    terms: list[dict[str, str]] = []

    for filepath in translation_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue

        section_match = _DISCOVERED_TERMS_PATTERN.search(content)
        if not section_match:
            continue

        section_text = section_match.group(1)

        # Skip "No new terms discovered" entries
        if "no new terms" in section_text.lower():
            continue

        for entry_match in _DISCOVERED_TERM_ENTRY.finditer(section_text):
            english = entry_match.group(1).strip()
            korean = entry_match.group(2).strip()

            if english and korean and english.lower() not in seen:
                seen.add(english.lower())
                terms.append({"english": english, "korean": korean})

    return terms


def merge_glossary_terms(
    glossary_path: str,
    new_terms: list[dict[str, str]],
) -> dict[str, Any]:
    """Safely merge new terms into theological glossary (atomic write).

    P1 Compliance: YAML parsing + deduplication + sorted insertion.
    Uses atomic write (tmp + os.replace) to prevent corruption.

    SOT Compliance: Only Orchestrator should call this function.
    @sermon-translator instances are read-only on the glossary.

    Args:
        glossary_path: Path to theological-glossary.yaml
        new_terms: List of {"english": str, "korean": str} to add

    Returns:
        {
            "success": bool,
            "added": int,
            "skipped_duplicates": int,
            "total_entries": int,
            "error": str | None,
        }
    """
    result: dict[str, Any] = {
        "success": False,
        "added": 0,
        "skipped_duplicates": 0,
        "total_entries": 0,
        "error": None,
    }

    if not new_terms:
        result["success"] = True
        return result

    # Read existing glossary
    existing: dict[str, str] = {}
    comments: list[str] = []

    if os.path.isfile(glossary_path):
        try:
            with open(glossary_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.rstrip("\n")
                    if stripped.startswith("#") or not stripped.strip():
                        comments.append(stripped)
                    else:
                        # Parse "key": "value" format
                        kv_match = re.match(
                            r'^"([^"]+)":\s*"([^"]*)"', stripped)
                        if kv_match:
                            existing[kv_match.group(1)] = kv_match.group(2)
        except OSError as e:
            result["error"] = f"Cannot read glossary: {e}"
            return result

    # Merge new terms
    added = 0
    skipped = 0

    for term in new_terms:
        english = term["english"]
        korean = term["korean"]
        if english in existing:
            skipped += 1
        else:
            existing[english] = korean
            added += 1

    result["added"] = added
    result["skipped_duplicates"] = skipped
    result["total_entries"] = len(existing)

    if added == 0:
        result["success"] = True
        return result

    # Write updated glossary (atomic)
    sorted_entries = sorted(existing.items(), key=lambda x: x[0].lower())

    lines = comments[:]
    if lines and lines[-1].strip():
        lines.append("")  # Blank line after comments

    # Add new terms marker
    lines.append(f"# === Auto-merged: {added} new terms "
                 f"({datetime.now(timezone.utc).strftime('%Y-%m-%d')}) ===")

    for eng, kor in sorted_entries:
        lines.append(f'"{eng}": "{kor}"')

    try:
        tmp = glossary_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        os.replace(tmp, glossary_path)
        result["success"] = True
    except OSError as e:
        result["error"] = f"Cannot write glossary: {e}"

    return result


def update_translation_state(
    session_path: str,
    phase: str,
    glossary_terms_added: int = 0,
    failed_file: Optional[str] = None,
) -> dict[str, Any]:
    """Update translation_state in session.json after a translation batch.

    P1 Compliance: Deterministic JSON read-modify-write. No AI judgment.
    SOT Compliance: Only Orchestrator calls this function.

    Args:
        session_path: Path to session.json
        phase: Phase key from TRANSLATION_TARGETS (e.g., "wave-1", "phase-2-message")
        glossary_terms_added: Number of new terms merged in this batch
        failed_file: If a translation failed after max retries, record filename

    Returns:
        {"success": bool, "error": str | None}
    """
    result: dict[str, Any] = {"success": False, "error": None}

    try:
        with open(session_path, "r", encoding="utf-8") as f:
            session = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        result["error"] = f"Cannot read session.json: {e}"
        return result

    # Ensure translation_state exists (backward compatibility with v2.0)
    if "translation_state" not in session:
        session["translation_state"] = {
            "completed_phases": [],
            "glossary_terms_added": 0,
            "glossary_updated_at": None,
            "failed_translations": [],
        }

    ts = session["translation_state"]

    # Record completed phase (idempotent — no duplicates)
    if phase not in ts["completed_phases"]:
        ts["completed_phases"].append(phase)

    # Update glossary stats
    if glossary_terms_added > 0:
        ts["glossary_terms_added"] = ts.get("glossary_terms_added", 0) + glossary_terms_added
        ts["glossary_updated_at"] = datetime.now(timezone.utc).isoformat()

    # Record failure (if any)
    if failed_file:
        ts.setdefault("failed_translations", []).append({
            "phase": phase,
            "file": failed_file,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # Atomic write
    try:
        tmp = session_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2, ensure_ascii=False)
        os.replace(tmp, session_path)
        result["success"] = True
    except OSError as e:
        result["error"] = f"Cannot write session.json: {e}"

    return result


# ===================================================================
# 13. TRANSLATION ORCHESTRATION — P1 Master Functions
# ===================================================================


def check_pending_translation(
    phase: str,
    output_dir: str,
) -> dict[str, Any]:
    """Check if translation is complete for a given phase.

    Reuses get_translation_targets() — no duplicated file mapping.
    P1 Compliance: Deterministic filesystem check only.

    Args:
        phase: Key from TRANSLATION_TARGETS (e.g., "wave-1")
        output_dir: Base output directory

    Returns:
        {
            "pending": bool,        # True if any .ko.md missing
            "phase": str,
            "total": int,
            "missing_files": [str], # Missing .ko.md paths
            "existing_files": [str],
        }
    """
    targets = get_translation_targets(phase, output_dir)
    missing: list[str] = []
    existing: list[str] = []

    for t in targets:
        if os.path.isfile(t["target"]):
            existing.append(t["target"])
        else:
            missing.append(t["target"])

    return {
        "pending": len(missing) > 0,
        "phase": phase,
        "total": len(targets),
        "missing_files": missing,
        "existing_files": existing,
    }


def prepare_translation_batch(
    phase: str,
    output_dir: str,
    glossary_path: str,
) -> dict[str, Any]:
    """P1 Master: Generate all inputs for a translation batch.

    Deterministically produces prompts and paths for every file
    in the given phase. The Orchestrator's only job is to dispatch
    Agent calls with the provided prompts.

    Internally calls:
      - check_pending_translation(phase, output_dir)
      - get_translation_targets(phase, output_dir)
      - build_translation_prompt(source, glossary, output_dir) × N

    P1 Compliance: Pure function composition — no AI judgment.
    SOT Compliance: Read-only — no file writes.

    Args:
        phase: Key from TRANSLATION_TARGETS (e.g., "wave-1")
        output_dir: Base output directory
        glossary_path: Path to theological-glossary.yaml

    Returns:
        {
            "phase": str,
            "total": int,
            "targets": [
                {
                    "source": str,       # English original path
                    "target": str,       # .ko.md output path
                    "prompt": str,       # @sermon-translator prompt
                    "pacs_log": str,     # pACS log path
                },
                ...
            ],
            "glossary_path": str,
            "skip_reason": str | None,   # Non-None if already complete
        }
    """
    result: dict[str, Any] = {
        "phase": phase,
        "total": 0,
        "targets": [],
        "glossary_path": glossary_path,
        "skip_reason": None,
    }

    # Check if phase exists in TRANSLATION_TARGETS
    if phase not in TRANSLATION_TARGETS:
        result["skip_reason"] = f"Unknown phase: {phase}"
        return result

    # Check if already complete
    pending = check_pending_translation(phase, output_dir)
    if not pending["pending"]:
        result["total"] = pending["total"]
        result["skip_reason"] = (
            f"All {pending['total']} translations already complete "
            f"for {phase}"
        )
        return result

    # Generate targets with prompts
    targets = get_translation_targets(phase, output_dir)
    result["total"] = len(targets)

    for t in targets:
        source = t["source"]
        target = t["target"]

        # Skip if .ko.md already exists (partial completion)
        if os.path.isfile(target):
            continue

        # Skip if English source doesn't exist
        if not os.path.isfile(source):
            continue

        prompt = build_translation_prompt(source, glossary_path, output_dir)

        # Derive pACS log path
        base = os.path.splitext(os.path.basename(source))[0]
        pacs_log = os.path.join(
            output_dir, "pacs-logs", f"translation-pacs-{base}.md"
        )

        result["targets"].append({
            "source": source,
            "target": target,
            "prompt": prompt,
            "pacs_log": pacs_log,
        })

    return result


def finalize_translation_batch(
    phase: str,
    output_dir: str,
    glossary_path: str,
    session_path: str,
) -> dict[str, Any]:
    """P1 Master: Validate, score, merge, and update after translation batch.

    Performs ALL post-translation steps deterministically:
      1. validate_translation_output() × N — structural checks
      2. extract_translation_pacs() × N — score extraction
      3. should_retranslate() × N — retry decisions
      4. collect_discovered_terms() — aggregate new terms
      5. merge_glossary_terms() — atomic glossary update
      6. update_translation_state() — session.json update

    The Orchestrator only needs to handle retranslate[] entries
    (re-dispatch Agent calls for RED-graded files).

    P1 Compliance: Pure deterministic pipeline — no AI judgment.
    SOT Compliance: Writes to glossary (atomic) and session.json
    only — Orchestrator sole writer.

    Args:
        phase: Key from TRANSLATION_TARGETS (e.g., "wave-1")
        output_dir: Base output directory
        glossary_path: Path to theological-glossary.yaml
        session_path: Path to session.json

    Returns:
        {
            "all_valid": bool,
            "results": [
                {
                    "source": str,
                    "target": str,
                    "valid": bool,
                    "pacs_grade": str,     # GREEN/YELLOW/RED
                    "pacs_score": int,     # min(Ft,Ct,Nt,Tt)
                    "errors": [str],
                },
                ...
            ],
            "retranslate": [
                {
                    "source": str,
                    "target": str,
                    "prompt": str,         # Re-translation prompt
                    "reason": str,
                },
                ...
            ],
            "glossary_update": {
                "terms_added": int,
                "terms_skipped": int,
            },
            "state_updated": bool,
            "error": str | None,
        }
    """
    output: dict[str, Any] = {
        "all_valid": True,
        "results": [],
        "retranslate": [],
        "glossary_update": {"terms_added": 0, "terms_skipped": 0},
        "state_updated": False,
        "error": None,
    }

    targets = get_translation_targets(phase, output_dir)
    ko_files: list[str] = []
    failed_file: Optional[str] = None

    for t in targets:
        source = t["source"]
        target = t["target"]
        entry: dict[str, Any] = {
            "source": source,
            "target": target,
            "valid": False,
            "pacs_grade": "RED",
            "pacs_score": 0,
            "errors": [],
        }

        # Step 1: Structural validation
        validation = validate_translation_output(source, target)
        entry["valid"] = validation["valid"]
        entry["errors"] = validation.get("errors", [])

        if not validation["valid"]:
            output["all_valid"] = False
            failed_file = os.path.basename(target)

            # Generate re-translation prompt
            prompt = build_translation_prompt(
                source, glossary_path, output_dir
            )
            output["retranslate"].append({
                "source": source,
                "target": target,
                "prompt": prompt,
                "reason": f"Validation failed: {'; '.join(entry['errors'])}",
            })
            output["results"].append(entry)
            continue

        # Step 2: Extract pACS (try .ko.md first, fallback to pACS log)
        try:
            with open(target, "r", encoding="utf-8") as f:
                ko_content = f.read()
        except OSError as e:
            entry["errors"].append(f"Cannot read translation: {e}")
            output["all_valid"] = False
            output["results"].append(entry)
            continue

        pacs = extract_translation_pacs(ko_content)

        # Fallback: read from separate pACS log file if .ko.md has no scores
        if not pacs["success"]:
            base = os.path.splitext(os.path.basename(source))[0]
            pacs_log_path = os.path.join(
                output_dir, "pacs-logs", f"translation-pacs-{base}.md"
            )
            if os.path.isfile(pacs_log_path):
                try:
                    with open(pacs_log_path, "r", encoding="utf-8") as f:
                        pacs_log_content = f.read()
                    pacs = extract_translation_pacs(pacs_log_content)
                except OSError:
                    pass

        if pacs["success"]:
            entry["pacs_grade"] = pacs["grade"]
            entry["pacs_score"] = pacs["pacs"]
        else:
            entry["pacs_grade"] = "UNKNOWN"
            entry["pacs_score"] = 0
            entry["errors"].append(
                f"pACS extraction failed: {pacs.get('error')}"
            )

        # Step 3: Retry decision
        decision = should_retranslate(pacs, retry_count=0)
        if decision["retranslate"]:
            output["all_valid"] = False
            prompt = build_translation_prompt(
                source, glossary_path, output_dir
            )
            output["retranslate"].append({
                "source": source,
                "target": target,
                "prompt": prompt,
                "reason": decision["reason"],
            })
        else:
            ko_files.append(target)

        output["results"].append(entry)

    # Step 4: Collect discovered terms from valid translations
    terms: list[dict[str, str]] = []
    if ko_files:
        terms = collect_discovered_terms(ko_files)

    # Step 5: Merge glossary terms (atomic, Orchestrator sole writer)
    if terms:
        merge_result = merge_glossary_terms(glossary_path, terms)
        output["glossary_update"]["terms_added"] = merge_result.get(
            "added", 0
        )
        output["glossary_update"]["terms_skipped"] = merge_result.get(
            "skipped_duplicates", 0
        )

    # Step 6: Update translation state in session.json
    glossary_added = output["glossary_update"]["terms_added"]
    state_result = update_translation_state(
        session_path,
        phase,
        glossary_terms_added=glossary_added,
        failed_file=failed_file,
    )
    output["state_updated"] = state_result.get("success", False)
    if not state_result.get("success"):
        output["error"] = state_result.get("error")

    return output


# ===================================================================
# 15. SESSION DISCOVERY & CONTEXT RESOLUTION — P1 Master Functions
# ===================================================================


def find_active_session(base_dir: str = "sermon-output") -> dict[str, Any]:
    """Fallback: scan sermon-output/*/session.json when state.yaml is unavailable.

    Scans all subdirectories of base_dir for session.json files.
    Prefers non-completed sessions; among those, returns most recently created.
    If all completed, returns most recently created completed session.

    P1 Compliance: 100% deterministic. Filesystem + JSON parsing only.
    SOT Compliance: Read-only. Modifies nothing.

    Args:
        base_dir: Parent directory to scan (default: "sermon-output")

    Returns:
        {
            "found": bool,
            "session_dir": str,      # e.g., "sermon-output/Romans-8-1-10-2026-03-06"
            "session_path": str,     # e.g., "sermon-output/.../session.json"
            "status": str,           # "initialized"|"running"|"completed"|"unknown"
            "created_at": str,       # ISO timestamp from session.json
        }
    """
    result: dict[str, Any] = {
        "found": False,
        "session_dir": "",
        "session_path": "",
        "status": "",
        "created_at": "",
    }

    if not os.path.isdir(base_dir):
        return result

    candidates: list[dict[str, str]] = []
    try:
        entries = list(os.scandir(base_dir))
    except OSError:
        return result

    for entry in entries:
        if not entry.is_dir():
            continue
        sp = os.path.join(entry.path, "session.json")
        if not os.path.isfile(sp):
            continue
        try:
            with open(sp, "r", encoding="utf-8") as f:
                data = json.load(f)
            candidates.append({
                "session_dir": entry.path,
                "session_path": sp,
                "status": data.get("status", "unknown"),
                "created_at": data.get("created_at", ""),
            })
        except (OSError, json.JSONDecodeError):
            continue

    if not candidates:
        return result

    # Prefer non-completed sessions; among those, most recently created
    active = [c for c in candidates if c["status"] != "completed"]
    chosen = max(active or candidates, key=lambda c: c["created_at"])

    result["found"] = True
    result["session_dir"] = chosen["session_dir"]
    result["session_path"] = chosen["session_path"]
    result["status"] = chosen["status"]
    result["created_at"] = chosen["created_at"]
    return result


def _build_sermon_path_map(output_dir: str) -> dict[str, str]:
    """Build deterministic path map for all sermon artifacts.

    Internal helper for resolve_sermon_context().
    P1 Compliance: Pure string operations. No filesystem access.

    Args:
        output_dir: Base output directory (e.g., "sermon-output/Romans-8-1-10-2026-03-06")

    Returns:
        Dict mapping artifact names to absolute paths.
    """
    rp = os.path.join(output_dir, "research-package")
    return {
        "session_json": os.path.join(output_dir, "session.json"),
        "checklist": os.path.join(output_dir, "todo-checklist.md"),
        "research_synthesis": os.path.join(output_dir, "research-synthesis.md"),
        "research_synthesis_ko": os.path.join(output_dir, "research-synthesis.ko.md"),
        "core_message": os.path.join(output_dir, "core-message.md"),
        "core_message_ko": os.path.join(output_dir, "core-message.ko.md"),
        "sermon_outline": os.path.join(output_dir, "sermon-outline.md"),
        "sermon_outline_ko": os.path.join(output_dir, "sermon-outline.ko.md"),
        "sermon_draft": os.path.join(output_dir, "sermon-draft.md"),
        "sermon_draft_ko": os.path.join(output_dir, "sermon-draft.ko.md"),
        "sermon_final": os.path.join(output_dir, "sermon-final.md"),
        "sermon_final_ko": os.path.join(output_dir, "sermon-final.ko.md"),
        "review_report": os.path.join(output_dir, "review-report.md"),
        "review_report_ko": os.path.join(output_dir, "review-report.ko.md"),
        "research_package": rp,
        "pacs_logs": os.path.join(output_dir, "pacs-logs"),
    }


def resolve_sermon_context(
    state_yaml_path: str = "state.yaml",
    fallback_base: str = "sermon-output",
) -> dict[str, Any]:
    """P1 Master: Resolve all sermon paths and state for resume/status.

    Single entry point for /sermon-resume and /sermon-status.
    The Orchestrator calls this ONCE and receives complete context.

    Normal flow:
      1. Read state.yaml -> extract sermon.output_dir
      2. Build deterministic path map from output_dir
      3. Read session.json -> domain state
      4. Read todo-checklist.md -> progress calculation

    Fallback flow (state.yaml missing/corrupt):
      1. find_active_session() -> scan subdirectories
      2. Continue with normal flow steps 2-4

    P1 Compliance: 100% deterministic. File reads + parsing only.
    SOT Compliance: Read-only. Modifies nothing.

    Args:
        state_yaml_path: Path to state.yaml (default: project root)
        fallback_base: Base directory for fallback scan

    Returns:
        {
            "found": bool,
            "output_dir": str,
            "session": dict,              # session.json full content
            "progress": dict,             # get_checklist_progress() result
            "paths": dict,                # All artifact paths (from _build_sermon_path_map)
            "translation_state": dict,    # session.json translation_state section
            "source": str,                # "state_yaml" or "fallback_scan"
            "error": str | None,
        }
    """
    result: dict[str, Any] = {
        "found": False,
        "output_dir": "",
        "session": {},
        "progress": {},
        "paths": {},
        "translation_state": {},
        "source": "",
        "error": None,
    }

    output_dir = ""
    source = ""

    # Primary: read state.yaml
    if os.path.isfile(state_yaml_path):
        try:
            import yaml
        except ImportError:
            yaml = None  # type: ignore[assignment]

        if yaml is not None:
            try:
                with open(state_yaml_path, "r", encoding="utf-8") as f:
                    state = yaml.safe_load(f)
                if isinstance(state, dict):
                    sermon = state.get("workflow", {}).get("sermon", {})
                    candidate = sermon.get("output_dir", "")
                    if isinstance(candidate, str) and candidate.strip():
                        output_dir = candidate.strip()
                        source = "state_yaml"
            except Exception:
                pass  # Fall through to fallback

    # Fallback: scan sermon-output/*/session.json
    if not output_dir:
        scan = find_active_session(fallback_base)
        if scan["found"]:
            output_dir = scan["session_dir"]
            source = "fallback_scan"

    if not output_dir:
        result["error"] = (
            f"No sermon session found. state.yaml at '{state_yaml_path}' "
            f"has no sermon.output_dir, and no session.json found in '{fallback_base}/*/'"
        )
        return result

    result["output_dir"] = output_dir
    result["source"] = source

    # Build deterministic path map
    paths = _build_sermon_path_map(output_dir)
    result["paths"] = paths

    # Read session.json
    session_path = paths["session_json"]
    if os.path.isfile(session_path):
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                result["session"] = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            result["error"] = f"Cannot read session.json: {e}"
            return result
    else:
        result["error"] = f"session.json not found at: {session_path}"
        return result

    # Extract translation_state
    result["translation_state"] = result["session"].get("translation_state", {
        "completed_phases": [],
        "glossary_terms_added": 0,
        "glossary_updated_at": None,
        "failed_translations": [],
    })

    # Read checklist progress
    checklist_path = paths["checklist"]
    result["progress"] = get_checklist_progress(checklist_path)

    result["found"] = True
    return result
