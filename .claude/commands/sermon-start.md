# /sermon-start — Sermon Research Workflow Entry Point

Start the Sermon Research Workflow. This command initializes Phase 0 and begins orchestration.

## Usage
```
/sermon-start [mode] [input]
```

## Arguments
- **mode**: `theme` (default) | `passage` | `series`
- **input**: The topic, passage reference, or series description

## Examples
```
/sermon-start theme Trusting God in times of suffering
/sermon-start passage Psalm 23:1-6
/sermon-start series John Gospel series - Week 3 (John 3:1-21)
```

## Execution

1. Load the sermon-orchestrator skill
2. Detect input mode using `_sermon_lib.detect_input_mode()` if not specified
3. **P1 Master — single call for all Phase 0 setup**:
   ```python
   result = _sermon_lib.initialize_sermon_output(user_input, mode, options)
   # Creates: output directory (collision-safe), session.json, todo-checklist.md
   # Returns: output_dir, session_path, checklist_path, state_yaml_sermon
   ```
4. Write `result["state_yaml_sermon"]` to state.yaml `workflow.sermon` section
5. Validate: `_sermon_lib.validate_sermon_sot_schema(state["workflow"]["sermon"])`
6. Check `user-resource/` for user-provided materials
7. If Mode A: dispatch `@passage-finder` for candidate passages
8. If Mode C: dispatch `@series-analyzer` for series context
9. If Mode B: proceed directly to HITL-1 with provided passage
10. Present HITL-1 options to user

**CRITICAL**: Do NOT manually call `get_output_dir_name()`, `create_output_structure()`,
`generate_session_json()`, or `generate_checklist()` individually.
Use `result["output_dir"]` as the `output_dir` for all subsequent function calls.

## SOT Initialization
```yaml
# Orchestrator writes result["state_yaml_sermon"] here:
workflow:
  name: "sermon-research"
  current_step: 1
  status: "running"
  sermon:
    mode: "{detected_mode}"
    output_dir: "{result.output_dir}"  # e.g., "sermon-output/Romans-8-1-10-2026-03-06"
    completed_gates: []
    srcs_threshold: 70
```
