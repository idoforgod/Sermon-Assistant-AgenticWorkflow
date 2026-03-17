# Sermon Assistant

**AI 기반 설교 비서 자동화 시스템** — 본문 선정부터 최종 원고까지, 11개 박사급 전문 에이전트가 체계적으로 성경연구를 돕습니다.

[AgenticWorkflow](AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md) 프레임워크(만능줄기세포)에서 분화된 자식 시스템입니다.
부모의 전체 DNA(절대 기준, 품질 보장, 안전장치, 기억 체계)를 구조적으로 내장하면서,
설교 연구 도메인에 특화된 GRA(Grounded Research Architecture)로 할루시네이션을 원천 차단합니다.

## 핵심 기능

- **11개 전문 연구 영역**: 원문 분석(히브리어/헬라어), 사본학, 구조 분석, 평행 본문, 신학, 문학 비평, 수사학, 역사 맥락, 핵심 단어, 성경지리, 문화 배경
- **GRA 3계층 품질 보증**: Agent Self-Verification → Cross-Validation Gates → SRCS 4축 평가
- **Hallucination Firewall**: 생성 시점에서 "모든 학자가 동의" 같은 패턴 차단
- **GroundedClaim 스키마**: 모든 연구 결과에 출처·신뢰도·불확실성 구조화
- **7개 HITL 체크포인트**: 본문 선정 → 연구 검토 → 스타일/메시지 → 아웃라인 → 포맷/최종 승인
- **3가지 입력 모드**: 주제 기반(Theme), 본문 직접 입력(Passage), 설교 시리즈(Series)
- **스타일 학습**: 기존 설교 샘플 분석 → 문체·어조 반영
- **Context Reset Recovery**: 세션 중단 시 자동 복구 (`/sermon-resume`)

## 빠른 시작

```bash
git clone https://github.com/idoforgod/Sermon-Assistant-AgenticWorkflow.git
cd Sermon-Assistant-AgenticWorkflow
claude          # Claude Code 실행
```

```
# 주제 기반 시작
/sermon-start theme 고난 중에도 하나님을 신뢰하는 것

# 본문 직접 입력
/sermon-start passage 시편 23:1-6

# 설교 시리즈
/sermon-start series 요한복음 강해 시리즈 - 3주차 (요 3:1-21)

# 또는 자연어로
시작하자
```

## 워크플로우 구조

```
Phase 0: 초기화 → 3-File Architecture 설정
    │
Phase 1: Research
    ├── Wave 1 (병렬): 원문 분석, 사본 비교, 성경지리, 역사문화 배경
    │       └── Cross-Validation Gate 1
    ├── Wave 2 (병렬): 구조 분석, 평행 본문, 핵심 단어
    │       └── Cross-Validation Gate 2
    ├── Wave 3 (병렬): 신학적 분석, 문학적 분석, 역사/문화 맥락
    │       └── Cross-Validation Gate 3
    ├── Wave 4 (순차): 플롯/수사학적 분석
    │       └── SRCS 4축 평가
    └── 연구 종합 (2000-2500자 압축)
    │
Phase 2: Planning → 스타일 선택 → 핵심 메시지 도출 → 아웃라인 설계
    │
Phase 2.5: Style Analysis (조건부) → 사용자 설교 스타일 반영
    │
Phase 3: Implementation → 원고 작성 → 품질 검토 → 최종 원고
```

## 프로젝트 구조

```
Sermon-Assistant-AgenticWorkflow/
├── README.md                                    ← 이 파일 (자식 시스템 진입점)
├── SERMON-ASSISTANT-ARCHITECTURE-AND-PHILOSOPHY.md  ← 설교 시스템 설계 철학·아키텍처
├── SERMON-ASSISTANT-USER-MANUAL.md              ← 설교 시스템 사용법
├── AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md   ← 부모 프레임워크 설계 철학
├── AGENTICWORKFLOW-USER-MANUAL.md               ← 부모 프레임워크 사용법
├── CLAUDE.md                                    ← Claude Code 전용 지시서
├── AGENTS.md                                    ← 모든 AI 에이전트 공통 지시서
├── soul.md                                      ← DNA 유전 정의
├── DECISION-LOG.md                              ← 설계 결정 로그 (ADR)
├── prompt/
│   └── workflow.md                              ← Sermon Research Workflow v2.0 (설계도)
├── .claude/
│   ├── settings.json                            ← Hook 설정
│   ├── agents/                                  ← 24개 에이전트 정의
│   │   ├── original-text-analyst.md             (히브리어/헬라어 원문 분석)
│   │   ├── manuscript-comparator.md             (번역본/사본 비교)
│   │   ├── structure-analyst.md                 (구조 분석)
│   │   ├── parallel-passage-analyst.md          (평행 본문 분석)
│   │   ├── theological-analyst.md               (신학적 분석)
│   │   ├── literary-analyst.md                  (문학적 분석)
│   │   ├── rhetorical-analyst.md                (플롯/수사학)
│   │   ├── historical-context-analyst.md        (역사/문화 맥락)
│   │   ├── keyword-expert.md                    (핵심 단어 연구)
│   │   ├── biblical-geography-expert.md         (성경지리)
│   │   ├── historical-cultural-expert.md        (역사문화적 배경)
│   │   ├── passage-finder.md                    (본문 탐색)
│   │   ├── series-analyzer.md                   (시리즈 맥락 분석)
│   │   ├── unified-srcs-evaluator.md            (SRCS 통합 평가)
│   │   ├── research-synthesizer.md              (연구 종합)
│   │   ├── message-synthesizer.md               (핵심 메시지 도출)
│   │   ├── outline-architect.md                 (아웃라인 설계)
│   │   ├── style-analyzer.md                    (스타일 분석)
│   │   ├── sermon-writer.md                     (원고 작성)
│   │   ├── sermon-reviewer.md                   (품질 검토)
│   │   ├── reviewer.md                          (공통: 적대적 리뷰어)
│   │   ├── translator.md                        (공통: 영→한 번역)
│   │   ├── sermon-translator.md                 (신학 전문 번역, theological-glossary 기반)
│   │   ├── fact-checker.md                      (공통: 사실 검증)
│   │   └── references/gra-compliance.md         (GRA 프로토콜)
│   ├── commands/                                ← 슬래시 커맨드
│   │   ├── sermon-start.md                      (/sermon-start)
│   │   ├── sermon-select-passage.md             (/sermon-select-passage)
│   │   ├── sermon-review-research.md            (/sermon-review-research)
│   │   ├── sermon-set-style.md                  (/sermon-set-style)
│   │   ├── sermon-confirm-message.md            (/sermon-confirm-message)
│   │   ├── sermon-approve-outline.md            (/sermon-approve-outline)
│   │   ├── sermon-set-format.md                 (/sermon-set-format)
│   │   ├── sermon-finalize.md                   (/sermon-finalize)
│   │   ├── sermon-status.md                     (/sermon-status)
│   │   ├── sermon-resume.md                     (/sermon-resume)
│   │   ├── sermon-learn-style.md                (/sermon-learn-style)
│   │   ├── sermon-evaluate-srcs.md              (/sermon-evaluate-srcs)
│   │   ├── start.md                             (Smart Router)
│   │   ├── install.md                           (/install)
│   │   └── maintenance.md                       (/maintenance)
│   ├── hooks/scripts/                           ← Hook + 검증 스크립트
│   │   ├── _sermon_lib.py                       (설교 워크플로우 결정론적 라이브러리, 2,984줄)
│   │   ├── context_guard.py                     (Hook 통합 디스패처)
│   │   ├── _context_lib.py                      (공유 라이브러리)
│   │   ├── save_context.py                      (SessionEnd/PreCompact 저장)
│   │   ├── restore_context.py                   (SessionStart 복원 + RLM)
│   │   ├── update_work_log.py                   (PostToolUse 작업 로그)
│   │   ├── generate_context_summary.py          (Stop 증분 스냅샷)
│   │   ├── output_secret_filter.py              (시크릿 탐지)
│   │   ├── block_destructive_commands.py        (위험 명령 차단)
│   │   └── ... (22개 Hook + 3개 테스트)
│   ├── skills/
│   │   ├── sermon-orchestrator/SKILL.md         (설교 오케스트레이터 스킬)
│   │   ├── workflow-generator/                  (워크플로우 생성 스킬)
│   │   └── doctoral-writing/                    (박사급 글쓰기 스킬)
│   └── context-snapshots/                       ← 런타임 (gitignored)
├── tests/                                       ← 4계층 테스트 (216개)
│   ├── test_layer1_unit.py                      (단위 테스트)
│   ├── test_layer2_e2e_hooks.py                 (E2E Hook 테스트)
│   ├── test_layer3_integration.py               (통합 테스트)
│   └── test_layer4_structural.py                (구조 일관성 테스트)
├── translations/
│   ├── glossary.yaml                            ← 번역 용어 사전
│   └── theological-glossary.yaml                ← 신학 번역 용어 사전 (SOT: Orchestrator)
├── coding-resource/                             ← 이론적 기반 자료
└── sermon-output/                               ← 워크플로우 산출물 (gitignored)
    └── [passage-YYYY-MM-DD]/                    ← 설교별 하위 디렉터리 (자동 생성)
        ├── research-package/                    (연구 결과물)
        ├── pacs-logs/                           (품질 평가 로그)
        ├── _temp/                               (임시 파일)
        └── session.json                         (도메인 상태 SOT)
```

## 스킬

| 스킬 | 설명 |
|------|------|
| **sermon-orchestrator** | 설교연구 워크플로우 총괄 오케스트레이션. Phase 0→1→2→3 전체 흐름 관리, GRA 품질 게이트, HITL 체크포인트 |
| **workflow-generator** | AgenticWorkflow 프레임워크의 핵심 스킬. Research → Planning → Implementation 3단계 구조의 `workflow.md` 설계·생성 |
| **doctoral-writing** | 박사급 학위 논문의 학문적 엄밀성과 명료성을 갖춘 글쓰기 지원 |

## 커맨드 레퍼런스

| 커맨드 | 설명 | HITL |
|--------|------|------|
| `/sermon-start` | 설교연구 워크플로우 시작 | - |
| `/sermon-select-passage` | 본문 선정 및 연구 옵션 설정 | HITL-1 |
| `/sermon-review-research` | 연구 결과 검토 | HITL-2 |
| `/sermon-set-style` | 설교 유형 및 청중 설정 | HITL-3a |
| `/sermon-confirm-message` | 핵심 메시지 확정 | HITL-3b |
| `/sermon-approve-outline` | 아웃라인 승인 | HITL-4 |
| `/sermon-set-format` | 원고 형식 및 분량 설정 | HITL-5a |
| `/sermon-finalize` | 최종 검토 및 완료 | HITL-5b |
| `/sermon-status` | 진행 상태 확인 | - |
| `/sermon-resume` | 컨텍스트 리셋 후 재개 | - |
| `/sermon-learn-style` | 설교 스타일 수동 분석 | - |
| `/sermon-evaluate-srcs` | SRCS 평가 수동 실행 | - |

## Context Preservation System

AgenticWorkflow 프레임워크로부터 상속받은 자동 저장·복원 시스템입니다. 컨텍스트 토큰 초과, `/clear`, 컨텍스트 압축 시 작업 내역이 상실되는 것을 방지합니다.

| 스크립트 | 트리거 | 역할 |
|---------|--------|------|
| `context_guard.py` | (Hook 디스패처) | Hook 통합 진입점 |
| `save_context.py` | SessionEnd, PreCompact | 전체 스냅샷 저장 |
| `restore_context.py` | SessionStart | RLM 패턴으로 복원 |
| `update_work_log.py` | PostToolUse | 9개 도구 작업 로그 누적 |
| `generate_context_summary.py` | Stop | 증분 스냅샷 + Knowledge Archive |
| `_sermon_lib.py` | (설교 전용 라이브러리) | GRA 검증, 체크리스트, 세션 관리 |
| `output_secret_filter.py` | PostToolUse (Bash/Read) | 시크릿 탐지 (25+ 패턴) |
| `block_destructive_commands.py` | PreToolUse (Bash) | 위험 명령 차단 |
| `setup_init.py` | Setup (--init) | 인프라 건강 검증 |

**테스트 커버리지**: 4계층 216개 테스트 (L1 Unit + L2 E2E + L3 Integration + L4 Structural) + 설교 워크플로우 222개 테스트 (`_test_sermon_lib.py`) + Safety Hook 131개 자동화 테스트.

## 절대 기준

AgenticWorkflow로부터 유전된 최상위 규칙:

1. **품질 최우선** — 속도, 비용, 작업량보다 최종 설교 원고의 품질이 유일한 기준
2. **단일 파일 SOT** — state.yaml + session.json + todo-checklist.md 계층 구조
3. **코드 변경 프로토콜 (CCP)** — _sermon_lib.py 2,984줄 결정론적 검증
4. **품질 > SOT, CCP** — 세 기준이 충돌하면 품질이 우선

## AI 도구 호환성

**Hub-and-Spoke 패턴**으로 모든 AI CLI 도구에서 동일한 방법론이 자동 적용됩니다.

| AI CLI 도구 | 시스템 프롬프트 파일 |
|------------|-------------------|
| Claude Code | `CLAUDE.md` |
| Gemini CLI | `GEMINI.md` |
| Codex CLI | `AGENTS.md` |
| Copilot CLI | `.github/copilot-instructions.md` |
| Cursor | `.cursor/rules/agenticworkflow.mdc` |

## 문서 읽기 순서

| 순서 | 문서 | 목적 |
|------|------|------|
| 1 | **README.md** (이 파일) | 프로젝트 개요 파악 |
| 2 | [`SERMON-ASSISTANT-USER-MANUAL.md`](SERMON-ASSISTANT-USER-MANUAL.md) | 설교 시스템 사용법 학습 |
| 3 | [`SERMON-ASSISTANT-ARCHITECTURE-AND-PHILOSOPHY.md`](SERMON-ASSISTANT-ARCHITECTURE-AND-PHILOSOPHY.md) | 설교 시스템 설계 철학 이해 |
| 4 | [`AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md`](AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md) | 부모 프레임워크 설계 철학 (선택) |
| 5 | [`AGENTICWORKFLOW-USER-MANUAL.md`](AGENTICWORKFLOW-USER-MANUAL.md) | 부모 프레임워크 사용법 (선택) |
| 6 | [`soul.md`](soul.md) | DNA 유전 철학 (선택) |

> **부모-자식 문서 분리**: `AGENTICWORKFLOW-*.md`는 방법론/프레임워크를, `SERMON-ASSISTANT-*.md`는 도메인 고유 아키텍처를 기술합니다. 이 분리는 자식 시스템이 독립적으로 이해·운영될 수 있게 합니다.
