# /sermon-select-passage — HITL-1: Passage Selection

Select the sermon passage and configure research options.

## Checkpoint: HITL-1

## Display
Present passage candidates (if Mode A) with suitability analysis.
- Mode A: 한국어 번역본 (passage-candidates.ko.md) 기반으로 표시

## Options
```
[Passage Selection] Choose from candidates or enter directly

[Original Text Analysis Level]
- Standard: Word study + basic grammar analysis
- Advanced: Syntax + discourse analysis included
- Expert: Textual criticism included

[Research Scope]
- Full: All 11 research areas (recommended)
- Selective: Choose specific areas only
```

## After Selection
1. Record selection in session.json
2. Update state.yaml with passage and options
3. Update checklist (HITL-1 steps)
4. Begin Wave 1 execution (4 parallel research agents)
