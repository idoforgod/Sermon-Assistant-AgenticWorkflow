# /sermon-finalize — HITL-5b: Final Review

Review draft and finalize the sermon manuscript.

## Checkpoint: HITL-5b
## Context Reset Point: Yes

## Display
- Sermon draft (sermon-draft.ko.md — 한국어 번역본)
- Quality review report (review-report.ko.md — 한국어 번역본)
- Note: 영문 원본은 `.md`, 한국어 번역본은 `.ko.md`로 병렬 제공

## Options
```
[Review Result]
- Final approval - complete
- Request revisions - provide feedback
- Request full rewrite

[Revision Types]
- Supplement specific sections (specify)
- Replace illustrations/examples
- Adjust length (longer/shorter)
- Change style/tone
- Strengthen application points
```

## After Approval
1. Record in session.json context_snapshots (HITL-5b)
2. If revisions requested: dispatch @sermon-writer with feedback
3. If approved: @sermon-writer produces sermon-final.md
4. Update state.yaml status to "completed"
5. Mark all remaining checklist items complete
