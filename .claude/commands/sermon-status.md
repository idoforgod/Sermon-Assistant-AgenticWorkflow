# /sermon-status — Workflow Progress Status

Display current sermon research workflow progress.

## Usage
```
/sermon-status
```

## Context Resolution
```python
ctx = _sermon_lib.resolve_sermon_context(state_yaml_path="state.yaml", fallback_base="sermon-output")
# Use ctx["paths"], ctx["session"], ctx["progress"], ctx["output_dir"]
```
Do NOT manually construct file paths. Use `ctx["paths"]` for all reads.

## Reads (via ctx["paths"])
- state.yaml (workflow state) — read by resolve_sermon_context internally
- session.json (domain context) — available as ctx["session"]
- todo-checklist.md (detailed progress) — available as ctx["progress"]

## Display

1. **Current Phase**: Phase 0/1/2/2.5/3
2. **Current Step**: N/155
3. **Progress**: N% complete
4. **Passage**: [selected passage or pending]
5. **Completed Waves**: [list]
6. **Completed Gates**: [list]
7. **Pending Gate Warning**: If a gate has not been executed before current step
8. **SRCS Status**: Overall score (if evaluated)
9. **Last HITL**: [checkpoint name and decision]
10. **Section Progress**: Per-section completion breakdown
11. **Translation Status**: Per-wave translation completeness
    - Uses `_sermon_lib.check_pending_translation()` for each completed wave
    - Display format: "Wave 1: 4/4 translated ✓" or "Wave 2: ⚠ 1/3 missing"
    - Also checks phase-2/3 translations if applicable

## Gate Enforcement
Uses `_sermon_lib.check_pending_gate()` to detect unexecuted gates.
If a gate is pending, displays a warning:
```
WARNING: Gate N has not been executed. Run the gate before proceeding.
```

## No Side Effects
This command only reads — it never modifies state.yaml, session.json, or checklist.
