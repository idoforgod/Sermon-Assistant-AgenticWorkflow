# /sermon-resume — Context Reset Recovery

Resume the sermon research workflow after a context reset.

## Usage
```
/sermon-resume
```

## Reads
- session.json (domain context + HITL snapshots + translation_state)
- todo-checklist.md (progress tracking)
- research-synthesis.md (research insights, if available)
- research-synthesis.ko.md (한국어 번역본, if available)
- Phase-specific .ko.md files (sermon-outline.ko.md, sermon-final.ko.md — per context reset point)

## Recovery Process

1. **P1 Master — single call for context resolution**:
   ```python
   ctx = _sermon_lib.resolve_sermon_context(
       state_yaml_path="state.yaml",
       fallback_base="sermon-output"
   )
   # Returns: output_dir, session, progress, paths, translation_state, source
   ```
   - Normal flow: reads `state.yaml` → `sermon.output_dir` → resolves all paths
   - Fallback flow: if state.yaml missing/corrupt, scans `sermon-output/*/session.json`

2. Use `ctx["paths"]` for all file reads (do NOT construct paths manually):
   - `ctx["paths"]["research_synthesis_ko"]` — 한국어 연구 요약
   - `ctx["paths"]["sermon_outline_ko"]` — 한국어 설교 개요
   - `ctx["paths"]["sermon_final_ko"]` — 한국어 최종 원고

3. Read research-synthesis.md (if exists) from `ctx["paths"]["research_synthesis"]`

4. Verify and recover translations (P1 Master Pattern):
   ```
   output_dir = ctx["output_dir"]
   For each phase in ["wave-1", "wave-2", "wave-3", "wave-4",
                       "phase-2-message", "phase-2-outline",
                       "phase-3-draft", "phase-3-review", "phase-3-final"]:
     pending = check_pending_translation(phase, output_dir)
     if pending["pending"]:
       Display: "⚠ 번역 누락: {phase} — {len(missing_files)} files"
       batch = prepare_translation_batch(phase, output_dir, glossary_path)
       For each target in batch["targets"]:
         Agent(subagent_type="translator", prompt=target["prompt"])
       result = finalize_translation_batch(phase, output_dir, glossary_path, ctx["paths"]["session_json"])
       Handle result["retranslate"] if any (max 2 retries)
   ```
   - Only check phases that should be complete based on current_step
   - Check `failed_translations` list for unresolved failures

5. Display recovery summary:
   ```
   Sermon Research Workflow — Context Recovery
   Passage: [passage]
   Mode: [mode]
   Source: [state_yaml | fallback_scan]
   Output Dir: [output_dir]
   Progress: [N]% (Step [M]/155)
   Last completed: [section name]
   Next step: [description]
   Translation: [M] phases complete, [N] terms added to glossary
   ```

6. Resume execution from the next incomplete step

## Context Reset Points
- After HITL-2: Load session.json + research-synthesis.md + research-synthesis.ko.md + checklist
- After HITL-3b: Load session.json + sermon-outline.md + sermon-outline.ko.md + synthesis + checklist
- After HITL-5b: Load session.json + sermon-final.md + sermon-final.ko.md + checklist

## RLM Pattern
This command provides domain-specific pointers on TOP of the framework's existing restore_context.py recovery. It does NOT modify or replace the framework's context preservation system.
