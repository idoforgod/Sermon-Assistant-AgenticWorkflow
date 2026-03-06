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
  5. Checklist Management (130-step todo-checklist.md per workflow.md table)
  6. Session Initialization (Phase 0 deterministic setup)
  7. Error Handling (agent-level 5 types + workflow-level 3 handlers)

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

# Checklist template section counts (workflow.md:1084-1099 table)
# Note: workflow.md titles this "120-step" but the table sums to 130.
# Gates, SRCS Evaluation, and Research Synthesis are implicit within
# the Wave/HITL step counts as documented in the source table.
CHECKLIST_SECTIONS = [
    ("Phase 0: Initialization", 6),
    ("Phase 0-A: Passage Search (Mode A)", 6),
    ("HITL-1: Passage Selection", 3),
    ("Wave 1: Independent Analysis", 16),
    ("Wave 2: Dependent Analysis", 12),
    ("Wave 3: Deep Analysis", 12),
    ("Wave 4: Integration Analysis", 6),
    ("HITL-2: Research Review", 8),
    ("Phase 2: Planning", 16),
    ("HITL-3a/3b: Style & Message", 10),
    ("Phase 2.5: Style Analysis", 4),
    ("HITL-4: Outline Approval", 3),
    ("Phase 3: Implementation", 18),
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
    """Generate the todo-checklist.md content (130 steps per workflow.md table).

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
        "version": "2.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "input": user_input,
        "options": options or {
            "analysis_level": "Standard",
            "research_scope": "full",
        },
        "context_snapshots": {},
        "status": "initialized",
    }


def get_output_dir_name(title: str) -> str:
    """Generate output directory name from sermon title.

    Format: sermon-output/[title-YYYY-MM-DD]/
    """
    safe_title = re.sub(r"[^\w\s가-힣-]", "", title).strip()
    safe_title = re.sub(r"\s+", "-", safe_title)[:50]
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"sermon-output/{safe_title}-{date_str}"


def create_output_structure(base_dir: str) -> dict[str, str]:
    """Create the output directory structure.

    Returns dict of created directory paths.
    Reference: workflow.md:706-730
    """
    dirs = {
        "root": base_dir,
        "research": os.path.join(base_dir, "research-package"),
        "temp": os.path.join(base_dir, "_temp"),
    }

    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    return dirs


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
            if "Wave 1" in section_name:
                return "wave-1"
            elif "Wave 2" in section_name:
                return "wave-2"
            elif "Wave 3" in section_name:
                return "wave-3"
            elif "Wave 4" in section_name:
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
    step = 1
    wave_end_steps: dict[str, int] = {}
    for section_name, count in CHECKLIST_SECTIONS:
        end = step + count - 1
        if "Wave 1" in section_name:
            wave_end_steps["gate-1"] = end
        elif "Wave 2" in section_name:
            wave_end_steps["gate-2"] = end
        elif "Wave 3" in section_name:
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
