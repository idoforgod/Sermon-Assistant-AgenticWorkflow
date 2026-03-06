# AgenticWorkflow

Claude Code 기반의 에이전트 워크플로우 자동화 프로젝트.

## 최종 목표

1. **워크플로우 설계**: 복잡한 작업을 Research → Planning → Implementation 3단계 구조의 `workflow.md`로 설계
2. **워크플로우 실행**: `workflow.md`에 정의된 에이전트·스크립트·자동화 구성을 **실제로 구현**

> 워크플로우를 만드는 것은 중간 산출물이다. **워크플로우에 기술된 내용이 실제로 동작하는 것**이 최종 목표다.

### 존재 이유 — DNA 유전

AgenticWorkflow는 **또 다른 agentic workflow system을 낳는 부모 유기체**다. `workflow-generator` 스킬이 생산 라인이며, 자식 시스템은 부모의 전체 게놈(헌법·구조·검증·안전·기억·비판·투명)을 **내장**한다. 상세: `soul.md §0`.

## 절대 기준

> 모든 설계·구현·수정 의사결정에 적용되는 최상위 규칙. 아래 모든 원칙보다 상위.

### 절대 기준 1: 최종 결과물의 품질
> **속도, 토큰 비용, 작업량, 분량 제한은 완전히 무시한다.** 유일한 기준은 **최종 결과물의 품질**이다.

### 절대 기준 2: 단일 파일 SOT + 계층적 메모리 구조
> 모든 공유 상태는 단일 파일(SOT)에 집중. SOT 쓰기는 Orchestrator/Team Lead만. 병렬 에이전트의 동일 파일 동시 수정 금지.

### 절대 기준 3: 코드 변경 프로토콜 (CCP)
> 코드를 작성·수정·추가·삭제하기 전에 **Step 1(의도 파악) → Step 2(영향 범위 분석) → Step 3(변경 설계)**를 내부적으로 수행. 분석 깊이는 변경 규모에 비례. **상세**: `docs/protocols/code-change-protocol.md`

**코딩 기준점 (CAP)**: CAP-1(코딩 전 사고), CAP-2(단순성 우선), CAP-3(목표 기반 실행), CAP-4(외과적 변경). 절대 기준 1과 충돌 시 품질이 우선.

### 절대 기준 간 우선순위
> **절대 기준 1(품질)이 최상위**. 절대 기준 2(SOT)와 3(CCP)은 품질을 보장하기 위한 동위 수단.

---

## 프로젝트 구조

```
AgenticWorkflow/
├── CLAUDE.md                        ← 이 파일 (Claude Code 지시서 — 경량 TOC)
├── AGENTS.md                        ← 모든 AI 에이전트 공통 지시서 (Hub — 방법론 SOT)
├── GEMINI.md                        ← Gemini CLI 전용 (Spoke)
├── soul.md                          ← DNA 유전 정의
├── DECISION-LOG.md                  ← 설계 결정 로그 (ADR)
├── AGENTICWORKFLOW-USER-MANUAL.md
├── AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md
├── docs/protocols/                  ← 상세 프로토콜 (on-demand 참조)
│   ├── autopilot-execution.md       (워크플로우 실행 체크리스트 + NEVER DO)
│   ├── quality-gates.md             (L0-L2 4계층 + P1 검증 14항목 상세)
│   ├── ulw-mode.md                  (ULW 강화 규칙 3개 + 런타임 메커니즘)
│   ├── context-preservation-detail.md (Hook 내부 메커니즘 + D-7 인스턴스)
│   └── code-change-protocol.md      (CCP 3단계 + CAP + 비례성 규칙)
├── .claude/
│   ├── settings.json                ← Hook 설정
│   ├── agents/
│   │   ├── translator.md            (영→한 번역, glossary 기반)
│   │   ├── sermon-translator.md     (신학 전문 번역, theological-glossary 기반)
│   │   ├── reviewer.md              (적대적 리뷰어, Enhanced L2)
│   │   └── fact-checker.md          (사실 검증, claim-by-claim)
│   ├── commands/
│   │   ├── install.md               (/install — Setup Init 검증)
│   │   └── maintenance.md           (/maintenance — 건강 검진)
│   ├── hooks/scripts/               ← Hook + 검증 스크립트
│   │   ├── context_guard.py         (통합 디스패처)
│   │   ├── _context_lib.py          (공유 라이브러리 — 파싱·생성·검증·압축)
│   │   ├── save_context.py          (SessionEnd/PreCompact 저장)
│   │   ├── restore_context.py       (SessionStart 복원 + RLM)
│   │   ├── update_work_log.py       (PostToolUse 9개 도구 추적)
│   │   ├── generate_context_summary.py (Stop 증분 스냅샷 + 안전망)
│   │   ├── diagnose_context.py      (Abductive Diagnosis 사전 분석)
│   │   ├── validate_diagnosis.py    (AD1-AD10 사후 검증)
│   │   ├── validate_pacs.py         (PA1-PA7 + L0 검증)
│   │   ├── validate_review.py       (R1-R5 리뷰 검증)
│   │   ├── validate_traceability.py (CT1-CT5 추적성 검증)
│   │   ├── validate_domain_knowledge.py (DK1-DK7 도메인 지식)
│   │   ├── validate_translation.py  (T1-T9 번역 검증)
│   │   ├── validate_verification.py (V1a-V1c 검증 로그)
│   │   ├── validate_workflow.py     (W1-W8 DNA 유전 검증)
│   │   ├── validate_retry_budget.py (RB1-RB3 재시도 예산)
│   │   ├── setup_init.py            (인프라 건강 검증 + SOT 쓰기 안전)
│   │   ├── setup_maintenance.py     (주기적 건강 검진)
│   │   ├── block_destructive_commands.py (위험 명령+네트워크+시스템 차단, exit 2)
│   │   ├── block_test_file_edit.py  (TDD Guard, .tdd-guard 토글)
│   │   ├── predictive_debug_guard.py (위험 파일 경고, exit 0)
│   │   ├── output_secret_filter.py  (시크릿 탐지, 3-tier 추출, 25+ 패턴, 2-패스 스캔, 131 테스트)
│   │   ├── security_sensitive_file_guard.py (보안 민감 파일 경고, 12 패턴)
│   │   ├── query_workflow.py        (워크플로우 관측성 — dashboard/weakest/retry/blocked, P1: SOT 스키마 검증 + context-aware pACS 추출)
│   │   ├── _test_secret_filter.py   (output_secret_filter 테스트 — 44개)
│   │   ├── _test_sensitive_file_guard.py (security_sensitive_file_guard 테스트 — 44개)
│   │   └── _test_block_destructive.py (block_destructive_commands 테스트 — 43개)
│   ├── context-snapshots/           ← 런타임 (gitignored)
│   └── skills/
│       ├── workflow-generator/      (워크플로우 설계·생성)
│       └── doctoral-writing/        (박사급 학술 글쓰기)
├── translations/glossary.yaml       ← 번역 용어 사전
├── translations/theological-glossary.yaml ← 신학 번역 용어 사전 (SOT: Orchestrator)
├── prompt/                          ← 프롬프트 자료
└── coding-resource/                 ← 이론적 기반 자료
```

## Context Preservation System

컨텍스트 토큰 초과·`/clear`·압축 시 작업 내역 상실을 방지하는 자동 저장·복원 시스템.

| Hook 이벤트 | 스크립트 | 동작 |
|------------|---------|------|
| Setup (`--init`) | `setup_init.py` | 인프라 건강 검증 + SOT 쓰기 안전 + 런타임 디렉터리 생성 |
| Setup (`--maintenance`) | `setup_maintenance.py` | 주기적 건강 검진 + doc-code 동기화 |
| PreToolUse (Bash) | `block_destructive_commands.py` | 위험 명령 차단 — 네트워크 유출+시스템 파괴+Git 파괴+치명적 rm (exit 2) |
| PreToolUse (Edit\|Write) | `block_test_file_edit.py` | TDD 모드 시 테스트 파일 보호 (exit 2) |
| PreToolUse (Edit\|Write) | `predictive_debug_guard.py` | 에러 이력 기반 위험 파일 경고 |
| SessionStart | `restore_context.py` | RLM 포인터 + 과거 세션 인덱스 + Predictive Debugging 캐시 |
| PostToolUse (9개 도구) | `update_work_log.py` | 작업 로그 누적 |
| PostToolUse (Bash\|Read) | `output_secret_filter.py` | 시크릿 탐지 (3-tier 추출, 25+ 패턴, 2-패스 스캔) |
| PostToolUse (Edit\|Write) | `security_sensitive_file_guard.py` | 보안 민감 파일 수정 경고 |
| Stop | `generate_context_summary.py` | 증분 스냅샷 + Knowledge Archive + 안전망 |
| PreCompact | `save_context.py` | 압축 전 스냅샷 저장 |
| SessionEnd | `save_context.py` | `/clear` 시 전체 스냅샷 저장 |

**필수 행동**: 세션 시작 시 `[CONTEXT RECOVERY]` 표시되면, 안내된 파일을 **반드시 Read tool로 읽어** 이전 맥락을 복원.

**상세**: Hook 내부 메커니즘, Knowledge Archive 필드, D-7 인스턴스 → `docs/protocols/context-preservation-detail.md`

## 자연어 라우팅 (Smart Router)

사용자가 "시작" 의도를 표현하면 `/start` 커맨드를 실행한다.

| 사용자 입력 패턴 | 라우팅 | 비고 |
|----------------|--------|------|
| "시작", "시작하자", "start", "begin", "작업 시작" | `/start` | 모드 안내 → 워크플로우 선택 |
| "설교 준비해줘", "시편 23편 설교" + 시작 의도 | `/start` → `/sermon-start` | 설교 입력이 명확하면 P4 적용 |
| "워크플로우 만들어줘", "자동화 파이프라인 설계" | `workflow-generator` 스킬 | 직접 스킬 진입 |
| "논문 스타일로 써줘", "학술적 글쓰기" | `doctoral-writing` 스킬 | 직접 스킬 진입 |

**P4 적용**: 사용자 의도가 명확하면 불필요한 질문 없이 바로 진행. 모호할 때만 모드 안내 표시.

## 설계 원칙

1. **P1 — 정확도를 위한 데이터 정제**: AI 전달 전 Python 등으로 노이즈 제거
2. **P2 — 전문성 기반 위임 구조**: 전문 에이전트에게 위임, Orchestrator는 조율만
3. **P3 — 이미지/리소스 정확성**: 정확한 다운로드 경로 명시, placeholder 불가
4. **P4 — 질문 설계 규칙**: 최대 4개 질문, 각 3개 선택지. 모호함 없으면 질문 없이 진행

## Autopilot Mode

워크플로우 실행 시 `(human)` 단계와 AskUserQuestion을 자동 승인하는 모드. 상세: `AGENTS.md §5.1`

**4계층 품질 보장**: L0(Anti-Skip Guard) → L1(Verification Gate) → L1.5(pACS Self-Rating) → L2(Calibration). 상세: `docs/protocols/quality-gates.md`

**워크플로우 실행 전 반드시 읽기**: `docs/protocols/autopilot-execution.md` — 단계별 체크리스트 + NEVER DO

## ULW (Ultrawork) Mode

프롬프트에 `ulw` 포함 시 활성화되는 **철저함 강도 오버레이**. Autopilot(자동화 축)과 직교. 3가지 강화 규칙: I-1(Sisyphus Persistence), I-2(Mandatory Task Decomposition), I-3(Bounded Retry Escalation).

**상세**: `docs/protocols/ulw-mode.md`

## 언어 및 스타일 규칙

- **프레임워크 문서·사용자 대화**: 한국어
- **워크플로우 실행**: 영어 (AI 성능 극대화 — 절대 기준 1 근거)
- **최종 산출물**: 영어 원본 + 한국어 번역 쌍 (`@translator` / `@sermon-translator`)
- **기술 용어**: 영어 유지 (SOT, Agent Team, Hooks 등)
- **시각화**: Mermaid 다이어그램 선호
- **깊이**: 간략 요약보다 포괄적·데이터 기반 서술 선호

### 번역 프로토콜

워크플로우에 `Translation: @translator`로 표기된 단계에 한해 `@translator` 서브에이전트 호출. 번역 대상은 텍스트 콘텐츠(`.md`, `.txt`)만. SOT `outputs.step-N-ko`에 기록. 용어 사전 `translations/glossary.yaml` 자동 유지.

#### 설교 워크플로우 전용 번역
- **에이전트**: `@sermon-translator` (신학 전문 번역 — `@translator` DNA 상속 + 도메인 특화)
- **용어 사전**: `translations/theological-glossary.yaml` (SOT: Orchestrator만 쓰기)
- **타이밍**: Wave Gate 통과 후 배치 번역 (Gate 실패 시 번역 낭비 방지)
- **출력**: 모든 `.md` 결과물에 대응하는 `.ko.md` 파일 생성
- **P1 함수**: `_sermon_lib.py`의 `get_translation_targets()`, `build_translation_prompt()`, `validate_translation_output()`, `extract_translation_pacs()`, `should_retranslate()`, `collect_discovered_terms()`, `merge_glossary_terms()`
- **P1 Master 함수** (2-Function Pattern): `check_pending_translation()`, `prepare_translation_batch()`, `finalize_translation_batch()` — 개별 함수 8개를 결정론적으로 조합, AI 판단 최소화
- **pACS**: 4축 (Ft=충실도, Ct=완전성, Nt=자연스러움, Tt=신학 정확도), grade = min(Ft,Ct,Nt,Tt)

## 스킬 개발 규칙

1. **모든 절대 기준을 반드시 포함** — 해당 도메인에 맞게 맥락화
2. **파일 간 역할 분담** 명확히 — SKILL.md(WHY), references/(WHAT/HOW/VERIFY)
3. **절대 기준 간 충돌 시나리오** 구체적으로 명시
4. 수정 후 반드시 **절대 기준 관점에서 성찰**
