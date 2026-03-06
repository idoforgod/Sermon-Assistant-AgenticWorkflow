# /start — Smart Workflow Router

설교연구 워크플로우 진입점. 실행 모드를 선택한 후 바로 워크플로우를 시작합니다.

## Natural Language Triggers

This command is invoked when the user says any of:
- "시작", "시작하자", "시작해", "시작해줘"
- "start", "let's start", "let's begin"
- "워크플로우 시작", "작업 시작", "작업을 시작하자"
- "begin", "go", "run"
- Or any variant expressing intent to start a workflow

## Execution Protocol

### Step 1: Intent Detection (P4 적용)

If the user's message already contains passage/theme info AND mode preference (e.g., "시편 23편으로 설교 준비해줘"), skip the mode guide and proceed directly to Step 3 with Interactive as default mode.

Otherwise, proceed to Step 2.

### Step 2: User Mode Guide

Present the following guide to the user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  설교연구 워크플로우 — 시작 안내
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  11명의 박사급 전문 에이전트가 체계적으로 설교를 준비합니다.
  입력: 주제/테마 | 본문(Pericope) | 설교시리즈
  출력: 연구 패키지 + 아웃라인 + 설교 원고

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
```

Wait for the user to choose an execution mode. If the user just says "1", "2", "3", or mode name, accept it and proceed.

### Step 3: Execute Sermon Workflow

Apply mode settings and execute `/sermon-start`:

| Mode selection | Action |
|----------------|--------|
| **Interactive** (default) | Execute `/sermon-start` with the user's input |
| **Autopilot** | Set `autopilot.enabled: true` in state.yaml, then execute `/sermon-start` |
| **ULW** | Activate ULW overlay per `docs/protocols/ulw-mode.md`, then execute `/sermon-start` |
| **Autopilot + ULW** | Both settings applied, then execute `/sermon-start` |

No separate confirmation step — proceed immediately after mode selection.
