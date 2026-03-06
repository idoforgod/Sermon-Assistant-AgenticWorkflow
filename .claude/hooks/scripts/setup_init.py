#!/usr/bin/env python3
"""
AgenticWorkflow Setup Init Hook — Infrastructure Health Validation

Triggered by: claude --init (or claude --init-only)
Location: .claude/settings.json (Project — project-specific validation)
Path: Direct execution, bypasses context_guard.py
      (Setup Hook is an independent concern from the global dispatcher)

SOT Compliance: NO ACCESS to SOT (state.yaml).
  Setup Hook validates INFRASTRUCTURE, not WORKFLOW STATE.
  SOT is relevant only at workflow execution time.
  Infrastructure validation operates at a layer below SOT.

PyYAML Independence: This script does NOT import PyYAML.
  Uses importlib.util.find_spec() for availability check only.

Quality Impact Path (절대 기준 1):
  Infrastructure validation → Silent Failure prevention →
  Context Preservation integrity → Session recovery accuracy →
  Infrastructure floor for workflow output quality
"""

import ast
import importlib.util
import json
import os
import re
import sys
from datetime import datetime


# =============================================================================
# Constants
# =============================================================================

# Hook scripts that must exist and have valid Python syntax (20 scripts)
# NOTE: setup_init.py and setup_maintenance.py are NOT in this list — they are
# the validators themselves (self-validating). P1-E detects them as "unregistered"
# but this is by design, not an error.
# D-7: Intentionally duplicated in setup_maintenance.py — setup scripts are
# independent from _context_lib.py by design (no import dependency).
REQUIRED_SCRIPTS = [
    "_context_lib.py",
    "block_destructive_commands.py",
    "block_test_file_edit.py",
    "context_guard.py",
    "output_secret_filter.py",
    "security_sensitive_file_guard.py",
    "diagnose_context.py",
    "generate_context_summary.py",
    "predictive_debug_guard.py",
    "query_workflow.py",
    "restore_context.py",
    "save_context.py",
    "update_work_log.py",
    "validate_diagnosis.py",
    "validate_domain_knowledge.py",
    "validate_pacs.py",
    "validate_retry_budget.py",
    "validate_review.py",
    "validate_traceability.py",
    "validate_translation.py",
    "validate_verification.py",
    "validate_workflow.py",
    "_sermon_lib.py",
    "validate_grounded_claim.py",
]

# Severity levels
CRITICAL = "CRITICAL"
WARNING = "WARNING"
INFO = "INFO"


# =============================================================================
# Main
# =============================================================================

def main():
    """Run all infrastructure validation checks."""
    input_data = _read_stdin_json()
    project_dir = os.environ.get(
        "CLAUDE_PROJECT_DIR",
        input_data.get("cwd", os.getcwd()),
    )

    results = []
    has_critical = False

    # 1. Python version
    results.append(_check_python_version())

    # 2. PyYAML availability (importlib.util.find_spec — NOT import)
    results.append(_check_pyyaml())

    # 3. Hook scripts existence + syntax validation (20 scripts)
    scripts_dir = os.path.join(project_dir, ".claude", "hooks", "scripts")
    for script_name in REQUIRED_SCRIPTS:
        result = _check_script(scripts_dir, script_name)
        results.append(result)
        if result["severity"] == CRITICAL and result["status"] == "FAIL":
            has_critical = True

    # 3b. REQUIRED_SCRIPTS completeness — detect unregistered .py files (P1-E)
    results.append(_check_scripts_completeness(scripts_dir))

    # 4. context-snapshots/ directory
    results.append(_check_snapshots_dir(project_dir))

    # 5. context-snapshots/sessions/ subdirectory
    results.append(_check_sessions_dir(project_dir))

    # 6. .gitignore check
    results.append(_check_gitignore(project_dir))

    # 7. SOT write safety (P1 Hallucination Prevention — 절대 기준 2)
    results.append(_check_sot_write_safety(scripts_dir))

    # 8. Runtime log directories (conditional — only when SOT exists)
    results.extend(_check_runtime_dirs(project_dir))

    # Write log file
    log_path = os.path.join(project_dir, ".claude", "hooks", "setup.init.log")
    _write_log(log_path, results)

    # Build summary
    critical_count = sum(1 for r in results if r["severity"] == CRITICAL and r["status"] == "FAIL")
    warning_count = sum(1 for r in results if r["severity"] == WARNING and r["status"] == "FAIL")
    pass_count = sum(1 for r in results if r["status"] == "PASS")

    summary = (
        f"Infrastructure validation: {pass_count}/{len(results)} passed"
        f" ({critical_count} critical, {warning_count} warning)"
    )

    # Output structured JSON for Claude Code (hookSpecificOutput protocol)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "Setup",
            "additionalContext": summary,
        }
    }
    print(json.dumps(output))

    if has_critical:
        # Report critical failures via stderr — Claude receives this as feedback
        critical_items = [r for r in results if r["severity"] == CRITICAL and r["status"] == "FAIL"]
        for item in critical_items:
            print(
                f"CRITICAL: {item['check']} — {item['message']}",
                file=sys.stderr,
            )
        sys.exit(2)

    sys.exit(0)


# =============================================================================
# Validation Checks
# =============================================================================

def _check_python_version():
    """Check Python version is 3.x."""
    major, minor = sys.version_info[:2]
    if major >= 3:
        return _result(INFO, "PASS", "Python version", f"Python {major}.{minor}")
    return _result(
        CRITICAL, "FAIL", "Python version",
        f"Python {major}.{minor} — Python 3.x required for hook scripts",
    )


def _check_pyyaml():
    """Check PyYAML availability without importing it.

    Uses importlib.util.find_spec() to avoid circular dependency:
    this script checks if PyYAML exists, so it must NOT depend on PyYAML.
    """
    spec = importlib.util.find_spec("yaml")
    if spec is not None:
        return _result(
            INFO, "PASS", "PyYAML",
            "installed — primary SOT parser available",
        )
    return _result(
        WARNING, "FAIL", "PyYAML",
        "not installed — SOT parsing will use regex fallback (degraded accuracy). "
        "Install with: pip install pyyaml",
    )


def _check_script(scripts_dir, script_name):
    """Check hook script exists and has valid Python syntax."""
    script_path = os.path.join(scripts_dir, script_name)

    if not os.path.exists(script_path):
        return _result(
            CRITICAL, "FAIL", f"Script: {script_name}",
            f"not found at {script_path}",
        )

    # Syntax validation via ast.parse (deterministic — P1 compliant)
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source, filename=script_name)
        size = os.path.getsize(script_path)
        return _result(
            INFO, "PASS", f"Script: {script_name}",
            f"valid syntax ({size:,} bytes)",
        )
    except SyntaxError as e:
        return _result(
            CRITICAL, "FAIL", f"Script: {script_name}",
            f"syntax error at line {e.lineno}: {e.msg}",
        )
    except Exception as e:
        return _result(
            CRITICAL, "FAIL", f"Script: {script_name}",
            f"cannot read: {e}",
        )


def _check_scripts_completeness(scripts_dir):
    """P1-E: Detect .py files in hooks/scripts/ not registered in REQUIRED_SCRIPTS.

    P1 Compliance: Deterministic filesystem scan + set comparison.
    Ignores __pycache__/, __init__.py, test files, and self-validating setup scripts.
    """
    # Setup scripts are self-validating — they cannot validate themselves
    _SELF_VALIDATING = {"setup_init.py", "setup_maintenance.py"}
    try:
        actual_files = set()
        for entry in os.listdir(scripts_dir):
            if (entry.endswith(".py")
                    and not entry.startswith("__")
                    and not entry.startswith("test_")
                    and not entry.startswith("_test_")
                    and entry not in _SELF_VALIDATING
                    and os.path.isfile(os.path.join(scripts_dir, entry))):
                actual_files.add(entry)
        registered = set(REQUIRED_SCRIPTS)
        unregistered = actual_files - registered
        if unregistered:
            return _result(
                WARNING, "WARN", "Scripts completeness",
                f"Unregistered .py files (add to REQUIRED_SCRIPTS): {', '.join(sorted(unregistered))}",
            )
        return _result(
            INFO, "PASS", "Scripts completeness",
            f"All {len(actual_files)} .py files registered in REQUIRED_SCRIPTS",
        )
    except Exception as e:
        return _result(
            WARNING, "WARN", "Scripts completeness",
            f"Cannot scan scripts directory: {e}",
        )


def _check_snapshots_dir(project_dir):
    """Check context-snapshots/ directory exists. Create if missing.

    NOTE: context-snapshots/ is NOT SOT. It's runtime infrastructure for
    Context Preservation System. Creating it is infra management, not state mutation.
    """
    snapshots_dir = os.path.join(project_dir, ".claude", "context-snapshots")

    if os.path.isdir(snapshots_dir):
        return _result(INFO, "PASS", "context-snapshots/", "directory exists")

    try:
        os.makedirs(snapshots_dir, exist_ok=True)
        return _result(INFO, "PASS", "context-snapshots/", "directory created")
    except Exception as e:
        return _result(
            CRITICAL, "FAIL", "context-snapshots/",
            f"cannot create directory: {e}",
        )


def _check_sessions_dir(project_dir):
    """Check context-snapshots/sessions/ subdirectory exists."""
    sessions_dir = os.path.join(
        project_dir, ".claude", "context-snapshots", "sessions"
    )

    if os.path.isdir(sessions_dir):
        return _result(INFO, "PASS", "sessions/", "directory exists")

    try:
        os.makedirs(sessions_dir, exist_ok=True)
        return _result(INFO, "PASS", "sessions/", "directory created")
    except Exception as e:
        return _result(
            WARNING, "FAIL", "sessions/",
            f"cannot create directory: {e}",
        )


def _check_runtime_dirs(project_dir):
    """Check workflow runtime log directories exist when SOT is present.

    Only activates when a SOT file (state.yaml/state.yml/state.json) exists,
    indicating an active workflow. Creates directories if missing.

    SOT Compliance: Checks SOT existence only (no content read).
    Directories created are NOT SOT — they are log infrastructure.
    """
    SOT_FILENAMES = ("state.yaml", "state.yml", "state.json")
    claude_dir = os.path.join(project_dir, ".claude")

    # Fast path: no SOT → no runtime dirs needed
    sot_exists = any(
        os.path.exists(os.path.join(claude_dir, fn))
        for fn in SOT_FILENAMES
    )
    if not sot_exists:
        return []

    results = []
    runtime_dirs = [
        "verification-logs",
        "pacs-logs",
        "review-logs",
        "autopilot-logs",
        "translations",
        "diagnosis-logs",
    ]

    for dirname in runtime_dirs:
        dirpath = os.path.join(project_dir, dirname)
        if os.path.isdir(dirpath):
            results.append(
                _result(INFO, "PASS", f"{dirname}/", "directory exists")
            )
        else:
            try:
                os.makedirs(dirpath, exist_ok=True)
                results.append(
                    _result(INFO, "PASS", f"{dirname}/", "directory created")
                )
            except Exception as e:
                results.append(
                    _result(
                        WARNING, "FAIL", f"{dirname}/",
                        f"cannot create directory: {e}",
                    )
                )

    return results


def _check_sot_write_safety(scripts_dir):
    """P1 Hallucination Prevention: Detect SOT write patterns in hook scripts.

    Defense-in-depth for 절대 기준 2 (SOT read-only for hooks).
    Two-tier deterministic text matching — not full static analysis.

    Tier 1: Non-SOT-aware scripts must not contain SOT filename strings at all.
    Tier 2: SOT-aware scripts — co-occurrence of SOT references + write patterns
            within the same function (AST function boundaries).

    Catches ~70% of common SOT write violations. Remaining 30% (indirect
    variable references) are covered by code review + user approval.
    """
    # D-7 intentional duplication — must match _context_lib.py:SOT_FILENAMES
    SOT_FILENAMES = ("state.yaml", "state.yml", "state.json")
    SOT_MARKERS = SOT_FILENAMES + ("sot_paths",)
    # Scripts that legitimately reference SOT for read-only access
    SOT_AWARE_SCRIPTS = {"_context_lib.py", "restore_context.py", "query_workflow.py"}
    WRITE_RE = re.compile(
        r'open\s*\([^)]*["\'](?:w|a)'      # open(..., "w"...) or open(..., "a"...)
        r'|atomic_write\s*\('               # atomic_write(...)
        r'|yaml\.dump\s*\(',                # yaml.dump(...)
    )

    violations = []

    for script_name in REQUIRED_SCRIPTS:
        script_path = os.path.join(scripts_dir, script_name)
        if not os.path.exists(script_path):
            continue
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception:
            continue

        if script_name in SOT_AWARE_SCRIPTS:
            # Tier 2: Function-scoped co-occurrence check via AST
            try:
                tree = ast.parse(source, filename=script_name)
                lines = source.split("\n")
                for node in ast.walk(tree):
                    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    if not hasattr(node, "end_lineno"):
                        continue  # Python < 3.8 graceful skip
                    func_text = "\n".join(lines[node.lineno - 1:node.end_lineno])
                    has_sot = any(m in func_text for m in SOT_MARKERS)
                    has_write = bool(WRITE_RE.search(func_text))
                    if has_sot and has_write:
                        violations.append(
                            f"{script_name}:{node.name}():{node.lineno}"
                        )
            except SyntaxError:
                pass  # Syntax errors caught by _check_script
        else:
            # Tier 1: Non-SOT scripts must not reference SOT filenames
            # Track triple-quote boundaries to skip docstring content
            lines = source.split("\n")
            in_docstring = False
            for i, line in enumerate(lines):
                stripped = line.strip()
                for quote in ('"""', "'''"):
                    if stripped.count(quote) % 2 == 1:
                        in_docstring = not in_docstring
                if in_docstring or stripped.startswith("#"):
                    continue
                for sot_name in SOT_FILENAMES:
                    if sot_name in line:
                        violations.append(
                            f"{script_name}:{i+1} references '{sot_name}'"
                        )

    if violations:
        return _result(
            WARNING, "FAIL", "SOT write safety",
            f"Potential SOT access violation: {'; '.join(violations[:3])}",
        )
    return _result(
        INFO, "PASS", "SOT write safety",
        "No SOT write patterns in hook scripts",
    )


def _check_gitignore(project_dir):
    """Check .gitignore includes context-snapshots/ pattern."""
    gitignore_path = os.path.join(project_dir, ".gitignore")

    if not os.path.exists(gitignore_path):
        return _result(
            WARNING, "FAIL", ".gitignore",
            "file not found — context-snapshots/ may be committed to git",
        )

    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()

        if "context-snapshots" in content:
            return _result(
                INFO, "PASS", ".gitignore",
                "includes context-snapshots/ pattern",
            )
        else:
            return _result(
                WARNING, "FAIL", ".gitignore",
                "does not include context-snapshots/ — snapshots may be committed",
            )
    except Exception as e:
        return _result(WARNING, "FAIL", ".gitignore", f"cannot read: {e}")


# =============================================================================
# Helpers
# =============================================================================

def _result(severity, status, check, message):
    """Create a structured validation result."""
    return {
        "severity": severity,
        "status": status,
        "check": check,
        "message": message,
    }


def _read_stdin_json():
    """Read JSON from stdin (Claude Code hook protocol)."""
    if sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, Exception):
        return {}


def _write_log(log_path, results):
    """Write validation results to log file.

    Log format is human-readable and machine-parseable by /install command.
    """
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        timestamp = datetime.now().isoformat()
        lines = [
            "# AgenticWorkflow Setup Init Log",
            f"# Timestamp: {timestamp}",
            f"# Python: {sys.version.split()[0]}",
            "",
        ]

        for r in results:
            marker = "PASS" if r["status"] == "PASS" else "FAIL"
            lines.append(
                f"[{r['severity']}] [{marker}] {r['check']}: {r['message']}"
            )

        lines.append("")

        # Summary
        pass_count = sum(1 for r in results if r["status"] == "PASS")
        fail_count = sum(1 for r in results if r["status"] == "FAIL")
        lines.append(f"# Summary: {pass_count} passed, {fail_count} failed, {len(results)} total")
        lines.append("")

        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception:
        pass  # Log write failure is non-blocking


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Setup init error: {e}", file=sys.stderr)
        sys.exit(2)
