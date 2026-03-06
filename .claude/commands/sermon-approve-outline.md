# /sermon-approve-outline — HITL-4: Outline Approval

Review and approve the sermon outline.

## Checkpoint: HITL-4

## Display
Full sermon outline from @outline-architect.
- 한국어 번역본 (sermon-outline.ko.md) 병렬 참조

## Options
```
[Outline Review]
- Approve - proceed to manuscript writing
- Request modifications - provide feedback
- Request restructure - different approach

[Fine-tuning]
- Reorder points
- Strengthen/reduce specific points
- Change illustrations/examples
```

## After Approval
1. Update state.yaml and checklist
2. Check for style samples in `user-sermon-style-sample/`
3. If samples exist: dispatch @style-analyzer (Phase 2.5)
4. Proceed to Phase 3: Implementation
