# Sermon Orchestrator Skill

Sermon Research Workflow v2.0 orchestration protocol. This skill guides the main Claude session (Orchestrator) through the complete sermon research workflow defined in `prompt/workflow.md`.

## Trigger
When the user invokes `/sermon-start` or requests sermon research workflow execution.

## Absolute Criteria (Inherited DNA)
1. **Quality**: Token cost and speed are completely ignored. Only final output quality matters.
2. **SOT**: `state.yaml` is the single source of truth. Only the Orchestrator (this session) writes to it.
3. **CCP**: All code changes follow the 3-step protocol (Intent → Impact → Plan).

## Architecture

```
Orchestrator (this session)
  ├── SOT Writer (state.yaml — sole writer)
  ├── Domain Context Manager (session.json — Orchestrator writes at HITL points)
  ├── Checklist Manager (todo-checklist.md — Orchestrator updates)
  └── Sub-agent Dispatcher (Task tool with subagent_type)
```

## Execution Protocol

### Phase 0: Initialization
1. Detect input mode: `_sermon_lib.detect_input_mode(user_input)`
2. Create output directory: `_sermon_lib.create_output_structure(base_dir)`
3. Generate session.json: `_sermon_lib.generate_session_json(mode, input)`
4. Generate checklist: `_sermon_lib.generate_checklist()` → write to `todo-checklist.md`
5. Initialize state.yaml with sermon workflow fields
6. Validate sermon SOT: `_sermon_lib.validate_sermon_sot_schema(state["workflow"]["sermon"])`
6. Check `user-resource/` for user-provided materials

### Phase 1: Research

#### Wave Execution Pattern (for each wave):
```
1. For each agent in the wave:
   Task(subagent_type="{agent-name}", prompt="""
     You are {agent-name}.
     Read .claude/agents/references/gra-compliance.md first.
     Passage: {passage_text}
     Analysis level: {level}
     Output to: {output_dir}/research-package/{output_file}
     {Wave 2+: Read dependency outputs first: {dependency_files}}
   """)

2. Wait for all agents to complete

3. For each agent output:
   a. Verify file exists and size > 100 bytes (L0)
   b. Parse claims and validate: _sermon_lib.validate_claims_batch()
   c. Check hallucination firewall: _sermon_lib.check_hallucination_firewall()
   d. Update checklist: _sermon_lib.update_checklist()
   e. Update state.yaml outputs

4. Run Cross-Validation Gate (HYBRID):
   a. CODE: _sermon_lib.validate_gate_structure(gate_name, output_dir)
   b. AI: Read all wave outputs, check for semantic contradictions
   c. CODE: _sermon_lib.validate_gate_result(gate, structural, semantic, findings)
   d. If gate FAILS: re-run conflicting agents with correction instructions
```

#### Wave Definitions
- **Wave 1** (parallel): original-text-analyst, manuscript-comparator, biblical-geography-expert, historical-cultural-expert → Gate 1
- **Wave 2** (parallel, depends Wave 1): structure-analyst, parallel-passage-analyst, keyword-expert → Gate 2
- **Wave 3** (parallel, depends Wave 2): theological-analyst, literary-analyst, historical-context-analyst → Gate 3
- **Wave 4** (sequential, depends Wave 3): rhetorical-analyst → SRCS Evaluation

#### SRCS Evaluation
```
Task(subagent_type="unified-srcs-evaluator", prompt="""
  Read all 11 research output files in {output_dir}/research-package/
  Evaluate all claims using SRCS 4-axis (CS, GS, US, VS).
  Check cross-consistency between agents.
  Output: srcs-summary.json + confidence-report.md
""")
```

#### Research Synthesis
```
Task(subagent_type="research-synthesizer", prompt="""
  Compress 11 research results into 2000-2500 characters.
  Output: research-synthesis.md
""")
```

### HITL Checkpoints

At each HITL checkpoint:
1. Display options to user (as defined in workflow.md)
2. Wait for user response (or auto-approve in Autopilot mode)
3. Record decision in session.json context_snapshots
4. Update state.yaml current_step
5. Update checklist

#### HITL Points
- **HITL-1**: Passage selection + research options
- **HITL-2**: Research results review (Context Reset Point)
- **HITL-3a**: Sermon style selection
- **HITL-3b**: Core message confirmation (Context Reset Point)
- **HITL-4**: Outline approval
- **HITL-5a**: Manuscript format selection
- **HITL-5b**: Final review (Context Reset Point)

### Phase 2: Planning
1. `/sermon-set-style` → HITL-3a
2. `@message-synthesizer` → core-message.md
3. `/sermon-confirm-message` → HITL-3b (Context Reset Point)
4. `@outline-architect` → sermon-outline.md
5. `/sermon-approve-outline` → HITL-4
6. Phase 2.5 (conditional): if `user-sermon-style-sample/` exists → `@style-analyzer`

### Phase 3: Implementation
1. `/sermon-set-format` → HITL-5a
2. `@sermon-writer` → sermon-draft.md
3. `@sermon-reviewer` → review-report.md
4. `/sermon-finalize` → HITL-5b (Context Reset Point)
5. If approved: `@sermon-writer` → sermon-final.md

## SOT Schema Validation

Call `_sermon_lib.validate_sermon_sot_schema(state["workflow"]["sermon"])` at these points:
1. **Phase 0**: After initializing state.yaml (step 6 above)
2. **After each HITL checkpoint**: When user decisions update sermon fields
3. **After gate completion**: When `completed_gates` is updated

If validation returns errors, fix the SOT before proceeding.

## SOT Schema (state.yaml additions for sermon workflow)

```yaml
workflow:
  name: "sermon-research"
  current_step: 1
  status: "running"
  outputs:
    step-1: "path/to/output.md"
  sermon:
    mode: "theme|passage|series"
    passage: "Psalm 23:1-6"
    output_dir: "sermon-output/trust-in-god-2026-03-06"
    completed_gates: ["gate-1", "gate-2"]
    srcs_threshold: 70
```

## Error Handling

### Agent-Level Failures

When a sub-agent returns a `[FAILURE:...]` tag:
1. Parse: `_sermon_lib.parse_agent_failure(output)`
2. Get handler: `_sermon_lib.get_failure_handler(failure_type)`
3. Execute handler action:
   - `return_partial`: Accept partial results, note gaps, continue
   - `seek_alternative`: Try alternative approach, fallback to skip_with_note
   - `request_retry`: Re-run agent with corrected input
   - `present_both_views`: Include both perspectives in output
   - `return_in_scope_only`: Accept in-scope portion only

### Workflow-Level Error Handlers (workflow.md §error_handlers)

These handle systemic issues that span multiple agents:

1. **`on_research_incomplete`** — When agents in a wave fail to complete:
   ```python
   result = _sermon_lib.handle_research_incomplete(completed_agents, expected_agents)
   # result["action"] == "partial_proceed" if ≥50% completed
   # result["action"] == "abort" if <50% completed
   ```

2. **`on_validation_failure`** — When a Cross-Validation Gate fails:
   ```python
   result = _sermon_lib.handle_validation_failure(gate_name, structural_passed, semantic_passed, findings)
   # result["action"] == "request_human_review"
   # Present result["summary"] to user for decision
   ```

3. **`on_srcs_below_threshold`** — When SRCS scores fall below threshold (70):
   ```python
   result = _sermon_lib.handle_srcs_below_threshold(agent_results, threshold=70.0)
   # result["action"] == "flag_for_review" if any agent below threshold
   # result["flagged_agents"] lists which agents need attention
   ```

## Gate Enforcement

Before advancing past a wave boundary, ALWAYS check:
```python
pending = _sermon_lib.check_pending_gate(current_step, completed_gates)
if pending:
    # STOP — execute the gate before proceeding
```

The `/sermon-status` command also reports pending gates.

## Context Reset Recovery

When context resets mid-workflow:
1. Framework's `restore_context.py` provides session pointer (automatic)
2. User invokes `/sermon-resume`
3. Read session.json, todo-checklist.md, research-synthesis.md
4. Determine last completed step from checklist
5. Resume from next step

## References
- `prompt/workflow.md` — Full workflow definition
- `.claude/agents/references/gra-compliance.md` — GRA protocol
- `.claude/hooks/scripts/_sermon_lib.py` — Deterministic functions
  - Note: `workflow.md` references `checklist_manager.py` (§996); this maps to `_sermon_lib.py` functions (`generate_checklist()`, `update_checklist()`, `check_pending_gate()`, etc.)
