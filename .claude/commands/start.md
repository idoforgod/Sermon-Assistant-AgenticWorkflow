# /start — Smart Workflow Router

Universal entry point for all workflows. Detects user intent and routes to the appropriate workflow with user mode selection.

## Natural Language Triggers

This command is invoked when the user says any of:
- "시작", "시작하자", "시작해", "시작해줘"
- "start", "let's start", "let's begin"
- "워크플로우 시작", "작업 시작", "작업을 시작하자"
- "begin", "go", "run"
- Or any variant expressing intent to start a workflow

## Execution Protocol

### Step 1: User Mode Guide (항상 먼저 표시)

Present the following guide to the user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AgenticWorkflow — 시작 안내
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[실행 모드 선택]

  1. Interactive (대화형) — 기본값
     모든 체크포인트에서 사용자 확인을 받습니다.
     결과를 직접 검토하고 피드백을 제공할 수 있습니다.
     → 처음 사용하거나 세밀한 제어가 필요할 때 추천

  2. Autopilot (자동 실행)
     체크포인트를 자동 승인하며 최소 개입으로 실행합니다.
     중간 결과를 건너뛰고 최종 결과물에 집중합니다.
     → 워크플로우에 익숙하고 빠른 실행을 원할 때 추천

  3. ULW (Ultra-Thorough)
     어떤 어려움도 포기하지 않는 Sisyphus Persistence.
     모든 작업을 세분화하고 체계적으로 재시도합니다.
     → 최고 품질이 필요한 중요한 작업에 추천

  * 모드 조합 가능: "Autopilot + ULW" = 자동이면서 최대 철저함

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[사용 가능한 워크플로우]

  A. 설교연구 워크플로우 (Sermon Research Workflow)
     11명의 박사급 전문 에이전트가 체계적으로 설교를 준비합니다.
     입력: 주제/테마 | 본문(Pericope) | 설교시리즈
     출력: 연구 패키지 + 아웃라인 + 설교 원고

  B. 워크플로우 생성기 (Workflow Generator)
     새로운 워크플로우를 설계하고 구현합니다.
     입력: 자동화하려는 작업 설명
     출력: workflow.md + 에이전트 + 스킬 + 커맨드

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 2: Collect User Selection

Wait for the user to choose:
1. **Execution mode**: Interactive (default) / Autopilot / ULW
2. **Workflow**: A (Sermon) / B (Generator) / or describe what they want

If the user's original message already contains enough context to determine both (e.g., "시편 23편으로 설교 준비해줘"), skip redundant questions and proceed.

Apply P4 (질문 설계 규칙): If intent is clear, don't ask unnecessary questions.

### Step 3: Route to Workflow

Based on selection:

| Selection | Action |
|-----------|--------|
| **A (Sermon)** | Execute `/sermon-start` with the user's input |
| **B (Generator)** | Invoke `workflow-generator` skill |
| **Mode includes "autopilot"** | Set `autopilot.enabled: true` in state.yaml |
| **Mode includes "ulw"** | Activate ULW overlay per `docs/protocols/ulw-mode.md` |

### Step 4: Confirm and Begin

Before routing, confirm:
```
[선택 확인]
  워크플로우: {selected_workflow}
  실행 모드: {selected_mode}
  입력: {user_input_summary}

  진행하시겠습니까? (Y/n)
```

If user confirms (or in Autopilot mode), proceed to the selected workflow entry point.
