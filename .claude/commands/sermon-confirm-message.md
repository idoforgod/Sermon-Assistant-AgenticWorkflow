# /sermon-confirm-message — HITL-3b: Core Message Confirmation

Confirm the Big Idea and sermon title.

## Checkpoint: HITL-3b
## Context Reset Point: Yes

## Display
- Big Idea options (2-3 from @message-synthesizer)
- Central Proposition
- Purpose Statement
- 한국어 번역본 (core-message.ko.md) 병렬 참조

## Options
```
[Big Idea Selection]
- Option A: [suggestion 1]
- Option B: [suggestion 2]
- Option C: [suggestion 3]
- Write my own

[Emphasis Adjustment]
- Theological depth emphasis
- Practical application emphasis
- Comfort and encouragement emphasis
- Challenge and decision emphasis
```

## After Confirmation
1. Record in session.json context_snapshots (HITL-3b)
2. Update state.yaml with confirmed Big Idea
3. Dispatch @outline-architect for sermon outline
