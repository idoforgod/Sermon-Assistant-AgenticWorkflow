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
2. **P1 Master — single call for all Phase 0 setup**:
   ```python
   result = _sermon_lib.initialize_sermon_output(user_input, mode, options)
   # Creates: output directory (collision-safe), session.json, todo-checklist.md
   # Returns: output_dir, session_path, checklist_path, state_yaml_sermon
   ```
3. Write `result["state_yaml_sermon"]` to state.yaml `workflow.sermon` section
4. Validate sermon SOT: `_sermon_lib.validate_sermon_sot_schema(state["workflow"]["sermon"])`
5. Check `user-resource/` for user-provided materials

**CRITICAL**: Do NOT manually call `get_output_dir_name()`, `create_output_structure()`,
`generate_session_json()`, or `generate_checklist()` individually. The P1 Master
`initialize_sermon_output()` encapsulates all of these to prevent path hallucination.
Use `result["output_dir"]` as the `output_dir` for all subsequent function calls.

### Phase 1: Research

#### Wave Execution Pattern (for each wave):
```
1. For each agent in the wave:
   prompt = _sermon_lib.build_research_agent_prompt(agent_name, passage, output_dir, level)
   Task(subagent_type="{agent-name}", prompt=prompt)

2. Wait for all agents to complete

3. For each agent output:
   result = _sermon_lib.validate_agent_output(filepath, agent_name)
   # This single call performs: L0 check + claim extraction + schema validation + hallucination firewall
   if not result["valid"]:
       handle errors per result["errors"]
   Update checklist: _sermon_lib.update_checklist()
   Update state.yaml outputs

4. Run Cross-Validation Gate (HYBRID):
   a. CODE: _sermon_lib.validate_gate_structure(gate_name, output_dir)
   b. AI: Read all wave outputs, check for semantic contradictions
   c. CODE: _sermon_lib.validate_gate_result(gate, structural, semantic, findings)
   d. CODE: _sermon_lib.record_gate_completion(sermon_state, gate_name)
   e. If gate FAILS: re-run conflicting agents with correction instructions
```

**P1 Hallucination Prevention**: Steps 1 and 3 are fully deterministic Python.
The Orchestrator MUST use `build_research_agent_prompt()` (not manual prompt construction)
and `validate_agent_output()` (not manual claim reading) to prevent hallucination.

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

## Translation Protocol

After each Gate pass and at key Phase 2/3 milestones, translate English outputs to Korean via `@sermon-translator`.

### Translation Timing
- **Wave N → Gate N pass → translate Wave N outputs** (batch, parallel)
- **Phase 2**: After `core-message.md` (before HITL-3b), after `sermon-outline.md` (before HITL-4)
- **Phase 3**: After `sermon-draft.md`, after `review-report.md` (before HITL-5b), after `sermon-final.md`

### P1 Translation Functions (deterministic — no AI judgment)
```python
# 1. Get files to translate for a given phase
targets = _sermon_lib.get_translation_targets(phase, output_dir)
# Returns: [{"source": "path/to/file.md", "target": "path/to/file.ko.md"}, ...]

# 2. Build deterministic prompt for @sermon-translator
prompt = _sermon_lib.build_translation_prompt(source_file, glossary_path, output_dir)

# 3. Validate translation output (L0 structural checks)
result = _sermon_lib.validate_translation_output(source_path, translation_path)
# Checks: file exists, size ratio 0.6-2.5x, heading structure preserved, code blocks preserved

# 4. Extract translation pACS (4-axis: Ft/Ct/Nt/Tt)
pacs = _sermon_lib.extract_translation_pacs(content)
# Returns: {"Ft": 95, "Ct": 90, "Nt": 85, "Tt": 90, "min_score": 85, "grade": "B+"}

# 5. Deterministic retry decision
decision = _sermon_lib.should_retranslate(pacs_result, retry_count, max_retries=2)
# Returns: {"should_retry": bool, "reason": str}

# 6. Collect discovered terms from all .ko.md files
terms = _sermon_lib.collect_discovered_terms(translation_files)

# 7. Merge new terms into glossary (Orchestrator-only, atomic)
result = _sermon_lib.merge_glossary_terms(glossary_path, new_terms)
```

### Wave Translation Pattern (2-Function Master)

Translation uses the P1 Master pattern to minimize AI judgment and prevent hallucination.
The Orchestrator calls exactly 2 Python functions; the only AI task is dispatching Agent calls.

```
1. PREPARE (P1 — deterministic):
   batch = prepare_translation_batch("wave-N", output_dir, glossary_path)
   if batch["skip_reason"]:
       log skip_reason → advance to next wave
       return

2. DISPATCH (AI — parallel Agent calls):
   For each target in batch["targets"]:
       Agent(subagent_type="translator", prompt=target["prompt"])

3. FINALIZE (P1 — deterministic):
   result = finalize_translation_batch("wave-N", output_dir, glossary_path, session_path)

4. HANDLE RETRANSLATION (if needed):
   if result["retranslate"]:
       For each entry in result["retranslate"]:
           Agent(subagent_type="translator", prompt=entry["prompt"])
       # Re-run finalize after retranslation (max 2 retries total)

5. BLOCKING GUARD — do NOT advance to next wave until:
   pending = check_pending_translation("wave-N", output_dir)
   assert pending["pending"] == False
```

**MANDATORY — NEVER SKIP**: This pattern executes after every Gate pass.
The 8 internal P1 functions (validate, pACS, retry, terms, glossary, state)
are called automatically inside prepare/finalize — the Orchestrator does not
call them individually.

### Glossary SOT Rule
- **Reader**: `@sermon-translator` (read-only, reports `## Discovered Terms` in output)
- **Writer**: Orchestrator only (calls `merge_glossary_terms()` atomically)
- **File**: `translations/theological-glossary.yaml`

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
3. Read session.json (includes `translation_state`), todo-checklist.md, research-synthesis.md
4. Verify and recover translations (P1 Master Pattern):
   - For each applicable phase: `pending = check_pending_translation(phase, output_dir)`
   - If `pending["pending"]`: run `prepare_translation_batch()` → dispatch Agents → `finalize_translation_batch()`
   - Check `failed_translations` for unresolved issues
5. Determine last completed step from checklist
6. Resume from next step

## References
- `prompt/workflow.md` — Full workflow definition
- `.claude/agents/references/gra-compliance.md` — GRA protocol
- `.claude/agents/sermon-translator.md` — Theological translation sub-agent
- `translations/theological-glossary.yaml` — Translation glossary (SOT: Orchestrator-only writes)
- `.claude/hooks/scripts/_sermon_lib.py` — Deterministic functions
  - Note: `workflow.md` references `checklist_manager.py` (§996); this maps to `_sermon_lib.py` functions (`generate_checklist()`, `update_checklist()`, `check_pending_gate()`, etc.)
  - P1 functions (hallucination prevention): `build_research_agent_prompt()`, `validate_agent_output()`, `extract_claims_from_output()`, `resolve_dependency_files()`, `record_gate_completion()`
  - P1 translation functions: `get_translation_targets()`, `build_translation_prompt()`, `validate_translation_output()`, `extract_translation_pacs()`, `should_retranslate()`, `collect_discovered_terms()`, `merge_glossary_terms()`, `update_translation_state()`
  - P1 translation master functions (2-Function Pattern): `check_pending_translation()`, `prepare_translation_batch()`, `finalize_translation_batch()`
