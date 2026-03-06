# AgenticWorkflow — AI 에이전트 공통 지시서

> 이 파일은 **모델·도구에 무관하게** 이 프로젝트에서 작업하는 모든 AI 에이전트가 따라야 할 규칙이다.
> Claude Code, Cursor, Copilot, Codex 등 어떤 도구를 사용하든 이 문서의 규칙이 적용된다.

---

## 1. 프로젝트 정의

에이전트 기반 워크플로우 자동화 프로젝트. 복잡한 작업을 체계적 워크플로우로 설계하고, 그 워크플로우를 실제로 구현하여 동작시키는 것이 목적이다.

### 최종 목표 — 2단계 프로세스

| 단계 | 산출물 | 성격 |
|------|--------|------|
| **Phase 1: 워크플로우 설계** | `workflow.md` | 중간 산출물 (설계도) |
| **Phase 2: 워크플로우 구현** | 에이전트·스크립트·자동화가 실제 동작하는 시스템 | **최종 산출물** |

> `workflow.md`를 만드는 것은 절반이다. **그 안에 기술된 내용이 실제로 동작하는 것**이 최종 목표다.

### 존재 이유 — DNA 유전

AgenticWorkflow는 자식 agentic workflow system을 낳는 **부모 유기체**다. 어떤 도메인의 자식이든, 부모의 전체 게놈을 구조적으로 내장한다.

| 게놈 구성요소 | 자식에 내장되는 형태 |
|-------------|-------------------|
| 절대 기준 3개 | workflow.md `Inherited DNA` 섹션 — 도메인별 맥락화 |
| SOT 패턴 | `state.yaml` — 단일 파일 + 단일 쓰기 지점 |
| 3단계 구조 | Research → Planning → Implementation 구조 제약 |
| 4계층 검증 | L0 Anti-Skip → L1 Verification → L1.5 pACS → L2 Review |
| P1 봉쇄 | Python 결정론적 검증 스크립트 |
| Safety Hook | 위험 명령 차단 + TDD Guard |
| Adversarial Review | `@reviewer` + `@fact-checker` Generator-Critic 패턴 |
| Decision Log | 자동 승인 결정의 근거 기록 |
| Context Preservation | 세션 간 기억 보존 + Knowledge Archive + RLM 패턴 |

> 유전은 선택이 아니라 **구조**다. 자식은 부모의 DNA를 "참고"하는 것이 아니라 **내장**한다. 상세: `soul.md §0`.

> **12→9 매핑**: soul.md §0의 12개 구성요소 중 위 9개가 `inherited_dna`로 자식에 구조적으로 내장된다. 나머지 3개 — 설계 원칙 P1-P4(절대 기준에 포함), Sisyphus/Error→Resolution(행동 패턴, 구조 아님), RLM 이론(이론적 기반, 구조 아님) — 는 부모 유기체의 내부 메커니즘으로서 자식에 암묵적으로 반영되되, 별도 `inherited_dna` 항목으로 분리하지 않는다. soul.md 자체는 메타 문서(유전의 정의서)이므로 유전 대상이 아니다.

### 워크플로우 기본 구조

모든 워크플로우는 3단계로 구성된다:

1. **Research** — 정보 수집 및 분석
2. **Planning** — 계획 수립, 구조화, 사람의 검토/승인
3. **Implementation** — 실제 실행 및 산출물 생성

각 단계에는 다음을 명시한다:
- 수행 작업 (Task)
- 담당 에이전트
- 데이터 전처리/후처리
- 산출물 (Output)
- 사람 개입 지점 (해당 시)

---

## 2. 절대 기준

> **이 프로젝트의 모든 설계·구현·수정 의사결정에 적용되는 최상위 규칙이다.**
> 아래의 모든 원칙, 가이드라인, 관례보다 상위에 있다.
> 어떤 원칙이든 절대 기준과 충돌하면, 절대 기준이 이긴다.

### 절대 기준 1: 최종 결과물의 품질

> **속도, 토큰 비용, 작업량, 분량 제한은 완전히 무시한다.**
> 모든 의사결정의 유일한 기준은 **최종 결과물의 품질**이다.
> 단계를 줄여서 빠르게 만드는 것보다, 단계를 늘려서라도 품질을 높이는 방향을 선택한다.

적용 예시:
- 워크플로우 단계가 많아져도 품질이 높아지면 → 단계 추가
- 에이전트를 더 써야 품질이 올라가면 → 에이전트 추가
- 검증 단계가 반복되어도 결과물이 나아지면 → 반복 허용

### 절대 기준 2: 단일 파일 SOT + 계층적 메모리 구조

> **단일 파일 SOT(Single Source of Truth) + 계층적 메모리 구조 설계 아래서, 수십 개의 에이전트가 동시에 작동해도 데이터 불일치가 발생하지 않는다.**

설계 규칙:
- **상태 집중**: 워크플로우의 모든 공유 상태는 **단일 파일**(예: `state.json`, `state.yaml`)에 집중한다. 여러 파일에 상태를 분산시키지 않는다.
- **단일 쓰기 지점**: SOT 파일에 대한 쓰기 권한은 Orchestrator(또는 지정된 단일 에이전트)만 갖는다. 다른 에이전트는 읽기 전용으로 접근하고, 자신의 결과를 별도 산출물 파일로 생성한다.
- **충돌 방지**: 복수 에이전트가 동일 파일을 동시에 수정하는 구조를 설계하지 않는다.

```
Bad:  Agent A → state.json 직접 수정
      Agent B → state.json 직접 수정  → 데이터 충돌

Good: Agent A → output-a.md 생성 → Orchestrator에 보고
      Agent B → output-b.md 생성 → Orchestrator에 보고
      Orchestrator → state.json에 병합  → 단일 쓰기 지점
```

### 절대 기준 3: 코드 변경 프로토콜 (Code Change Protocol)

> **코드를 작성·수정·추가·삭제하기 전에, 반드시 아래 3단계를 내부적으로 수행한다.**
> 이 프로토콜을 건너뛰는 것은 절대 기준 위반이다.

절대 기준 1(품질)이 "무엇을 최적화하는가"를 정의하고, 절대 기준 2(SOT)가 "데이터를 어떻게 구조화하는가"를 정의한다면, 절대 기준 3은 **"코드를 변경할 때 어떻게 행동하는가"**를 정의한다. 품질 높은 코드는 의존성·결합도·변경 파급 효과를 사전에 분석하는 엄밀한 프로세스에서 나온다.

#### 코딩 기준점 (Coding Anchor Points, CAP-1~4)

CCP가 "무엇을 수행하는가"(절차)를 정의한다면, CAP는 **"어떤 태도로 수행하는가"**(사고방식)를 정의한다. CCP의 모든 단계는 아래 4가지 기준점을 내면화한 상태에서 수행한다.

- **CAP-1: 코딩 전 사고** — 가정하지 않는다. 코드를 읽기 전에 수정하지 않으며, 트레이드오프가 있으면 표면화하고, 불명확하면 질문한다.
- **CAP-2: 단순성 우선** — 현재 요구를 충족하는 최소한의 코드만 작성한다. 추측성 기능, 조기 추상화, 불필요한 헬퍼를 만들지 않는다.
- **CAP-3: 목표 기반 실행** — 구현 전에 성공 기준을 정의하고, 구현 후에 검증한다 (예: 테스트, 수동 확인).
- **CAP-4: 외과적 변경** — 요청받은 변경만 수행한다. 관련 없는 코드를 "개선"하거나, 건드리지 않은 코드에 주석·타입·문서를 추가하지 않는다.

> CAP는 CCP의 하위 태도 규범이므로, 절대 기준 1(품질)과 충돌 시 품질이 이긴다. 예: CAP-2(단순성)가 품질을 저해하는 경우 — 품질을 위해 필요한 복잡성은 허용한다.

**Step 1 — 의도 파악:**
- 사용자가 지시한 구현사항을 정확하게 파악했는가? 1-2문장으로 명확하게 설명할 수 있어야 한다.
- 변경 목적(버그 수정, 리팩토링, 성능, 기능 추가 등)과 제약(호환성 유지 여부, 사용 기술 스택 등)을 정확하게 파악했는가?

**Step 2 — 영향 범위 분석 (Ripple Effect Analysis):**

신규 코드 작성 및 기존 코드 수정이 코드베이스 전체에 가져오는 영향을 조사한다:
- **직접 의존**: 수정 대상이 정의된 함수/클래스/모듈/파일
- **호출 관계**: 이 코드를 호출하거나, 이 코드가 호출하는 다른 코드
- **구조적 관계**: 상속/구현(inheritance, interface), 합성/구성(composition), 연관/참조(association)
- **데이터 모델/스키마**: 같이 변경되어야 할 타입/필드/검증 로직
- **테스트 코드**: 단위 테스트, 통합 테스트, 스냅샷 테스트 등
- **설정/환경/빌드**: config, DI 설정, 라우팅, 의존성 주입 등
- **문서/주석/API 스펙**: 주석, README, API 문서, 타입 정의 등

"여기를 바꾸었으니, 이 변경이 어디까지 파급될 수 있는지"를 전문가 수준에서 조사한다. 결합도가 높은 부분(강결합, 변경 결합, 샷건 서저리 가능성)이 있다면 **반드시** 사전 고지하여 사용자와 협의한다.

**Step 3 — 변경 설계 (Change Plan):**
- 연관된 실제 코드를 업데이트하기 전에, 단계별 변경 계획을 제안한다:
  - 1단계: 어떤 파일/클래스/함수부터 수정할지
  - 2단계: 하위 의존성/호출자에 어떤 변경을 전파할지
  - 3단계: 테스트/문서/설정을 어떻게 맞출지
- 결합도 감소 / 응집도 증가 관점에서 더 나은 구조로의 리팩토링 기회가 보이면 함께 제안한다 (실행은 사용자 승인 후).

**비례성 규칙 — 프로토콜은 항상 수행하되, 분석 깊이는 변경의 영향 범위에 비례한다:**

| 변경 규모 | 기준 | 적용 깊이 |
|----------|------|---------|
| **경미** | 오타, 주석, 포맷팅 등 로직 무관 변경 | Step 1만 — "파급 효과 없음" 1문장 확인 후 즉시 실행 |
| **표준** | 함수/로직 변경, 파일 추가/삭제 | 전체 3단계 수행 |
| **대규모** | 아키텍처, 공개 API, cross-cutting 변경 | 전체 3단계 + **반드시** 사전 사용자 승인 |

적용 예시:

```
Bad:  "사용자가 함수 수정을 요청 → 해당 함수만 수정 → 호출자 6곳이 런타임 에러"
Good: "사용자가 함수 수정을 요청 → 호출 관계 6곳 확인 → 영향 범위 고지 → 단계별 변경 계획 제안 → 승인 후 실행"
```

**커뮤니케이션 규칙:**
- 불필요하게 장황한 이론 설명은 피하고, 실질적인 코드와 구체적 단계 위주로 설명한다.
- 중요한 설계 선택에는 간단한 이유를 덧붙인다.
- 모호한 부분이 있어도 작업을 회피하지 말고, "합리적인 가정"을 명시한 뒤 최선의 설계를 제안한다.

### 절대 기준 간 우선순위

> **절대 기준 1(품질)이 최상위이다. 절대 기준 2(SOT)와 절대 기준 3(CCP)은 품질을 보장하기 위한 동위 수단이다.**

```
절대 기준 1 (품질) — 최상위. 모든 기준의 존재 이유.
  ├── 절대 기준 2 (SOT) — 데이터 무결성 보장 수단
  └── 절대 기준 3 (CCP) — 코드 변경 품질 보장 수단
```

절대 기준 2(SOT)와 3(CCP)은 서로 다른 차원에서 작동하므로 직접 충돌 가능성은 낮다. 어느 기준이든 절대 기준 1(품질)과 충돌하면 품질이 이긴다. SOT와 CCP 모두 품질을 보장하기 위한 **수단**이지, 품질을 제약하는 **목적**이 아니다.

충돌 시나리오와 해소:
- SOT 단일 쓰기 지점이 정보 병목을 일으켜 에이전트가 오래된 데이터로 작업 → **에이전트 간 산출물 직접 참조 허용** (SOT 구조 조정)
- 품질 향상을 위한 단계 추가로 SOT 상태 복잡도 증가 → **감수** (절대 기준 1 > 2)
- 완전 독립 병렬 작업(에이전트 간 공유 상태 없음)에서 SOT가 불필요 → **SOT 경량화 허용** (판단 근거 문서화)
- CCP의 전체 분석이 사소한 변경에 과도한 오버헤드 → **비례성 규칙 적용** (경미한 변경은 Step 1만)

---

## 3. 설계 원칙

절대 기준에 종속되는 하위 원칙이다.

### P1. 정확도를 위한 데이터 정제

큰 데이터를 AI에게 그대로 전달하면 노이즈로 정확도가 하락한다.

- 각 단계에 **전처리(pre-processing)** 명시: 에이전트에게 넘기기 전 노이즈 제거
- 각 단계에 **후처리(post-processing)** 명시: 산출물을 다음 단계에 전달하기 전 정제
- 코드로 사전 계산 가능한 연관관계는 미리 처리 → AI가 판단·분석에 집중

```
Bad:  "수집된 전체 웹페이지 HTML을 에이전트에 전달"
Good: "Python script로 본문만 추출 → 핵심 텍스트만 에이전트에 전달"
```

### P2. 전문성 기반 위임 구조

각 작업을 가장 잘 수행할 수 있는 전문 에이전트에게 위임하여 품질을 극대화한다. Orchestrator는 전체 품질을 조율하고, 전문 에이전트는 각자의 영역에 깊이 집중한다.

```
Orchestrator (품질 조율 + 흐름 관리)
  ├→ Agent A: 전문 리서치 (해당 도메인 최적화)
  ├→ Agent B: 심층 분석 (분석에만 집중)
  └→ Agent C: 검증 및 품질 게이트
```

#### Orchestrator 역할 정의

**Orchestrator = 메인 Claude 세션**이다. 별도 에이전트 파일이 아닌, 워크플로우를 실행하는 메인 세션이 Orchestrator 역할을 수행한다. `(team)` 단계에서는 **Orchestrator가 Team Lead 역할을 겸임**한다.

| 역할 | 주체 | SOT 쓰기 | 시작 시점 |
|------|------|---------|----------|
| Orchestrator | 메인 Claude 세션 | **쓰기 가능** (유일) | 워크플로우 시작 시 |
| Team Lead | Orchestrator 겸임 | **쓰기 가능** | `(team)` 단계 진입 시 |
| Sub-agent | `Task` 도구로 생성 | **읽기 전용** | Orchestrator가 호출 시 |
| Teammate | `Task` + `TeamCreate`로 생성 | **읽기 전용** | Team Lead가 할당 시 |

#### Sub-agent 호출 프로토콜

Orchestrator가 Sub-agent(`@translator`, `@reviewer`, `@fact-checker`)를 호출할 때의 표준 프로토콜:

**1. 호출 방법**: `Task` 도구의 `subagent_type` 파라미터로 에이전트 이름 지정
```
Task(subagent_type="translator", prompt="...", ...)
```

**2. 프롬프트에 반드시 포함할 컨텍스트**:
- 워크플로우 단계 번호 (step N)
- 입력 산출물 파일 경로 (절대 경로)
- 해당 단계의 Verification 기준 (있는 경우)
- SOT `outputs.step-N` 경로 (산출물 저장 위치)
- 참조 파일 경로 (glossary.yaml, 이전 단계 산출물 등)

**3. 결과 수신**: Sub-agent 종료 시 `Task` 도구가 결과를 반환한다.
- 산출물 파일이 디스크에 생성되었는지 Orchestrator가 확인
- P1 검증 스크립트 실행 (validate_review.py, validate_translation.py 등)
- SOT `outputs.step-N`에 경로 기록 (Orchestrator가 수행)

**4. `(team)` 단계 Task Lifecycle**:
```
Team Lead(=Orchestrator)
  1. TeamCreate → SOT active_team 기록
  2. TaskCreate (subject, description, owner=@teammate)
  3. Task(subagent_type, team_name, ...) → Teammate 생성
  4. Teammate: 작업 수행 → L1 자기 검증 → L1.5 pACS 자기 채점
  5. Teammate: SendMessage(보고 + pACS 점수) → TaskUpdate(completed)
  6. Team Lead: 보고 수신 → L2 종합 검증 → SOT 갱신
  7. TeamDelete → SOT active_team → completed_teams 이동
```

**Dense Checkpoint Pattern (DCP)**: 턴 수 > 10인 Task에 중간 체크포인트(CP-1/2/3) 삽입. 상세: `references/claude-code-patterns.md §DCP`

### P3. 리소스 정확성

이미지, 파일, 외부 리소스가 필요한 단계에서는 정확한 경로를 명시한다. placeholder 누락 불가.

### P4. 질문 설계 규칙

사용자에게 질문할 때:
- 최대 4개까지만
- 각 질문에 3개 정도의 선택지 제공
- 모호한 부분이 없으면 질문 없이 진행

---

## 4. 프로젝트 구조

```
AgenticWorkflow/
├── CLAUDE.md          ← Claude Code 전용 지시서
├── AGENTS.md          ← 이 파일 (모델 무관 공통 지시서)
├── README.md          ← 프로젝트 소개
├── AGENTICWORKFLOW-USER-MANUAL.md              ← 사용자 매뉴얼
├── AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md  ← 설계 철학 및 아키텍처 전체 조감도
├── DECISION-LOG.md          ← 프로젝트 설계 결정 로그 (ADR)
├── COPYRIGHT.md          ← 저작권
├── .claude/
│   ├── settings.json          ← Hook 설정 (Setup + SessionEnd)
│   ├── agents/                ← Sub-agent 정의
│   │   ├── translator.md     (영→한 번역 전문 에이전트 — glossary 기반 용어 일관성)
│   │   ├── reviewer.md       (Adversarial Review — 코드/산출물 비판적 분석, 읽기 전용)
│   │   └── fact-checker.md   (Adversarial Review — 외부 사실 검증, 웹 접근)
│   ├── commands/              ← Slash Commands
│   │   ├── install.md         (Setup Init 검증 결과 분석 — /install)
│   │   └── maintenance.md     (Setup Maintenance 건강 검진 — /maintenance)
│   ├── hooks/scripts/         ← Context Preservation System + Setup Hooks + Safety Hooks
│   │   ├── context_guard.py   (Hook 통합 디스패처 — 4개 이벤트의 단일 진입점)
│   │   ├── _context_lib.py    (공유 라이브러리 — 파싱, 생성, SOT 캡처, Smart Throttling, Autopilot 상태 읽기·검증, ULW 감지·준수 검증, 절삭 상수 중앙화, sot_paths() 경로 통합, 다단계 전환 감지, 결정 품질 태그 정렬, Error Taxonomy 12패턴+Resolution 매칭, Success Patterns(Edit/Write→Bash 성공 시퀀스 추출), IMMORTAL-aware 압축+감사 추적, E5 Guard 중앙화(is_rich_snapshot+update_latest_with_guard), Knowledge Archive 통합(archive_and_index_session — 부분 실패 격리), 경로 태그 추출(extract_path_tags), KI 스키마 검증(_validate_session_facts — RLM 필수 키 보장), SOT 스키마 검증(validate_sot_schema — 워크플로우 state.yaml 구조 무결성 8항목 검증: S1-S6 기본 + S7 pacs 5필드(dimensions, current_step_score, weak_dimension, history, pre_mortem_flag) + S8 active_team 5필드(name, status(partial|all_completed), tasks_completed, tasks_pending, completed_summaries)), Adversarial Review P1 검증(validate_review_output R1-R5, parse_review_verdict, calculate_pacs_delta, validate_review_sequence), Translation P1 검증(validate_translation_output T1-T7, check_glossary_freshness T8, verify_pacs_arithmetic T9 범용, validate_verification_log V1a-V1c), Predictive Debugging P1(aggregate_risk_scores+validate_risk_scores RS1-RS6+_RISK_WEIGHTS 13개 가중치+_RECENCY_DECAY_DAYS 감쇠), pACS P1 검증(validate_pacs_output PA1-PA6 — pACS 로그 구조 무결성: 파일 존재·최소 크기·차원 점수·Pre-mortem·min() 산술·Color Zone), L0 Anti-Skip Guard(validate_step_output L0a-L0c — 산출물 파일 존재+최소 크기+비공백), Team Summaries KI 아카이브(_extract_team_summaries — SOT active_team.completed_summaries → KI 보존), Abductive Diagnosis Layer(diagnose_failure_context 사전 증거 수집 + validate_diagnosis_log AD1-AD10 사후 검증 + _extract_diagnosis_patterns KA 아카이빙 + Fast-Path FP1-FP3 + 가설 우선순위 H1/H2/H3), 모듈 레벨 regex 컴파일(9개+8개+8개+4개+5개 패턴 — 프로세스당 1회))
│   │   ├── save_context.py    (저장 엔진)
│   │   ├── restore_context.py (복원 — RLM 포인터 + 완료/Git 상태 + Predictive Debugging 위험 점수 캐시 생성)
│   │   ├── update_work_log.py (작업 로그 누적 — 9개 도구 추적)
│   │   ├── generate_context_summary.py (증분 스냅샷 + Knowledge Archive + E5 Guard + Autopilot Decision Log 안전망 + ULW Compliance 안전망)
│   │   ├── setup_init.py      (Setup Init — 인프라 건강 검증 + SOT 쓰기 패턴 검증(P1 할루시네이션 봉쇄), --init 트리거)
│   │   ├── setup_maintenance.py (Setup Maintenance — 주기적 건강 검진, --maintenance 트리거)
│   │   ├── block_destructive_commands.py (PreToolUse Safety Hook — 위험 명령 차단(P1 할루시네이션 봉쇄), exit code 2로 차단 + Claude 자기 수정)
│   │   ├── block_test_file_edit.py  (PreToolUse TDD Guard — 테스트 파일 수정 차단(.tdd-guard 토글), exit code 2로 차단 + 구현 코드 수정 유도)
│   │   ├── predictive_debug_guard.py (PreToolUse Predictive Debug — 에러 이력 기반 위험 파일 경고, exit code 0 경고 전용)
│   │   ├── output_secret_filter.py  (PostToolUse 시크릿 탐지 — 3-tier 추출(tool_response→file read→transcript), 25+ regex 패턴, 2-패스 스캔(raw+base64/URL), fcntl-locked 감사 로그, exit code 0 경고 전용)
│   │   ├── security_sensitive_file_guard.py (PostToolUse 보안 민감 파일 경고 — .env/PEM/credentials/cloud/K8s/terraform 등 12 패턴, 세션 dedup, exit code 0 경고 전용)
│   │   ├── diagnose_context.py  (Abductive Diagnosis 사전 증거 수집 — 품질 게이트 FAIL 시 증거 번들 생성, Orchestrator 수동 호출)
│   │   ├── query_workflow.py    (워크플로우 관측성 — dashboard/weakest/retry/blocked 4모드, P1 SOT 스키마 검증 + context-aware pACS 추출)
│   │   ├── validate_pacs.py    (pACS P1 검증 + L0 Anti-Skip Guard — PA1-PA7, 독립 실행 스크립트, JSON 출력)
│   │   ├── validate_review.py (Adversarial Review P1 검증 — R1-R5, 독립 실행 스크립트, JSON 출력)
│   │   ├── validate_translation.py (Translation P1 검증 — T1-T9 + glossary 검증, JSON 출력)
│   │   ├── validate_verification.py (Verification Log P1 검증 — V1a-V1c 구조적 무결성, JSON 출력)
│   │   ├── validate_diagnosis.py (Abductive Diagnosis P1 사후 검증 — AD1-AD10, JSON 출력)
│   │   ├── validate_traceability.py (Cross-Step Traceability P1 검증 — CT1-CT5, JSON 출력)
│   │   ├── validate_domain_knowledge.py (Domain Knowledge P1 검증 — DK1-DK7, JSON 출력)
│   │   ├── validate_workflow.py (DNA 유전 P1 검증 — W1-W8, JSON 출력)
│   │   ├── validate_retry_budget.py (Retry Budget P1 검증 — RB1-RB3 재시도 예산 판정(ULW-aware), JSON 출력)
│   │   ├── _test_secret_filter.py   (output_secret_filter 테스트 — 44개)
│   │   ├── _test_sensitive_file_guard.py (security_sensitive_file_guard 테스트 — 44개)
│   │   └── _test_block_destructive.py (block_destructive_commands 테스트 — 43개)
│   ├── context-snapshots/     ← 런타임 스냅샷 (gitignored)
│   └── skills/
│       ├── workflow-generator/   ← 워크플로우 설계·생성
│       │   ├── SKILL.md          (스킬 정의 + 절대 기준)
│       │   └── references/       (구현 패턴, 템플릿, 문서 분석 가이드)
│       └── doctoral-writing/     ← 박사급 학술 글쓰기
│           ├── SKILL.md          (스킬 정의 + 절대 기준)
│           └── references/       (체크리스트, 빈출 오류, 수정 사례, 분야별 가이드)
├── prompt/              ← 프롬프트 자료
│   ├── crystalize-prompt.md      (프롬프트 압축 기법)
│   ├── distill-partner.md        (에센스 추출 및 최적화)
│   └── crawling-skill-sample.md  (크롤링 스킬 샘플)
└── coding-resource/     ← 참고 자료
```

### Context Preservation System

컨텍스트 윈도우 소진, 세션 초기화, 컨텍스트 압축 시 작업 맥락이 상실되는 문제를 방지하는 자동 저장·복원 시스템이다.

**핵심 원리:**
- RLM 패턴 적용: 작업 내역을 **외부 메모리 객체**(MD 파일)로 영속화하고, 새 세션에서 포인터 기반으로 복원
- P1 원칙 준수: 트랜스크립트 파싱·통계 산출은 Python 코드가 결정론적으로 수행. AI는 의미 해석에만 집중
- 절대 기준 2 준수: SOT 파일(`state.yaml`)은 **읽기 전용**으로만 접근. 스냅샷은 별도 디렉터리(`context-snapshots/`)에 저장
- **Knowledge Archive**: 세션 간 지식 축적 — `knowledge-index.jsonl`에 세션 사실을 결정론적으로 추출·축적. Stop hook과 SessionEnd/PreCompact 모두에서 기록하여 세션의 100% 인덱싱 보장. 각 엔트리에 completion_summary(도구 성공/실패), git_summary(변경 상태), session_duration_entries(세션 길이), phase(세션 단계), phase_flow(다단계 전환 흐름), primary_language(주요 파일 확장자), error_patterns(Error Taxonomy 12패턴 분류 + resolution 매칭), tool_sequence(RLE 압축 도구 시퀀스), final_status(success/incomplete/error/unknown), tags(경로 기반 검색 태그 — CamelCase/snake_case 분리 + 확장자 매핑) 포함. AI가 Grep으로 프로그래밍적 탐색 (RLM 패턴)
- **Resume Protocol**: 스냅샷에 결정론적 복원 지시 포함 — 수정/참조 파일 목록, 세션 메타데이터, 완료 상태(도구 성공/실패), Git 변경 상태. **동적 RLM 쿼리 힌트**: 수정 파일 경로에서 추출한 태그(`extract_path_tags()`)와 에러 정보를 기반으로 세션별 맞춤 Grep 쿼리 예시를 자동 생성. 복원 품질의 바닥선 보장
- **Autopilot 런타임 강화**: Autopilot 활성 시 스냅샷에 Autopilot 상태 섹션(IMMORTAL 우선순위)을 포함하고, 세션 복원 시 실행 규칙을 컨텍스트에 주입. Stop hook이 Decision Log 누락을 감지·보완
- **ULW 모드 감지·보존**: `detect_ulw_mode()`가 트랜스크립트에서 word-boundary 정규식으로 `ulw` 키워드를 감지. 활성 시 스냅샷에 ULW 상태 섹션(IMMORTAL 우선순위)을 포함하고, SessionStart가 3개 강화 규칙(Intensifiers)을 컨텍스트에 주입. `check_ulw_compliance()`가 준수를 결정론적으로 검증. Knowledge Archive에 `ulw_active: true` 태깅
- **결정 품질 태그 정렬**: 스냅샷의 "주요 설계 결정" 섹션은 `[explicit]` > `[decision]` > `[rationale]` > `[intent]` 순으로 정렬하여, 15개 슬롯에 고신호 결정이 우선 배치됨. 비교·트레이드오프·선택 패턴도 추출
- **IMMORTAL-aware 압축**: 스냅샷 크기 초과 시 IMMORTAL 섹션을 우선 보존하고 비-IMMORTAL 콘텐츠를 먼저 절삭. 극단적 경우에도 IMMORTAL 텍스트 시작 부분 보존. **압축 감사 추적**: 각 압축 Phase가 제거한 문자 수를 HTML 주석(`<!-- compression-audit: ... -->`)으로 스냅샷 끝에 기록 (Phase 1~7 단계별 delta + 최종 크기)
- **Error Taxonomy**: 도구 에러를 12패턴으로 분류 (file_not_found, permission, syntax, timeout, dependency, edit_mismatch, type_error, value_error, connection, memory, git_error, command_not_found). False positive 방지를 위해 negative lookahead·한정어 매칭 적용. Knowledge Archive의 error_patterns 필드에 기록. **Error→Resolution 매칭**: 에러 발생 후 5 entries 이내의 성공적 도구 호출을 file-aware 매칭으로 탐지하여 `resolution` 필드에 기록 (도구명 + 파일명). `Grep "resolution" knowledge-index.jsonl`로 해결 패턴 cross-session 탐색 가능
- **시스템 명령 필터링**: 스냅샷의 "현재 작업" 섹션에서 `/clear`, `/help` 등 시스템 명령을 필터링하여 실제 작업 의도만 캡처
- **Crash-safe 쓰기**: 모든 파일 쓰기(스냅샷, 아카이브, 로그 정리)에 atomic write(temp → rename) 패턴 적용. 프로세스 크래시 시 부분 쓰기 방지
- **P1 할루시네이션 봉쇄 (Hallucination Prevention)**: 반복적으로 100% 정확해야 하는 작업을 Python 코드로 강제한다. (1) **KI 스키마 검증**: `_validate_session_facts()`가 knowledge-index 쓰기 직전 RLM 필수 키(session_id, tags, final_status 등 10개) 존재를 보장 — 누락 시 안전 기본값 채움. (2) **부분 실패 격리**: `archive_and_index_session()`에서 archive 파일 쓰기 실패가 knowledge-index 갱신을 차단하지 않음 — RLM 핵심 자산 보호. (3) **SOT 쓰기 패턴 검증**: `setup_init.py`의 `_check_sot_write_safety()`가 Hook 스크립트에서 SOT 파일명 + 쓰기 패턴 공존을 AST 함수 경계 기반으로 탐지. (4) **SOT 스키마 검증**: `validate_sot_schema()`가 워크플로우 state.yaml의 구조적 무결성을 8항목으로 검증 (S1-S6 기본 + S7 pacs 5필드 + S8 active_team 5필드). (5) **Adversarial Review P1 검증**: `validate_review_output()` R1-R5, `parse_review_verdict()`, `calculate_pacs_delta()`, `validate_review_sequence()`가 리뷰 품질을 결정론적으로 보장

**데이터 흐름:**

```
작업 진행 중 ─→ [PostToolUse] update_work_log.py ─→ work_log.jsonl 누적 (9개 도구 추적)
             ├→ [PostToolUse] output_secret_filter.py ─→ Bash|Read 출력 시크릿 탐지 (3-tier 추출, 25+ 패턴, 독립 실행)
             └→ [PostToolUse] security_sensitive_file_guard.py ─→ Edit|Write 민감 파일 경고 (독립 실행)
                                                     │ (토큰 75% 초과 시)
                                                     ↓
응답 완료 ────→ [Stop] generate_context_summary.py ─→ latest.md 저장 (30초 throttling)
                                                     │        + knowledge-index.jsonl 축적
                                                     │        + sessions/ 아카이빙
                                                     │        + E5 Empty Snapshot Guard
                                                     ↓
세션 종료/압축 ─→ [SessionEnd/PreCompact] save_context.py ─→ latest.md 저장
                                                     │        + knowledge-index.jsonl 축적
                                                     │        + sessions/ 아카이빙
                                                     ↓
새 세션 시작 ──→ [SessionStart] restore_context.py ───────→ 포인터+요약+완료상태+Git상태 출력
                                                     AI가 Read tool로 전체 복원
```

---

## 5. 구현 요소 매핑

워크플로우 설계 시 아래 구현 요소를 조합한다. 도구마다 명칭이 다르지만 개념은 동일하다.

| 워크플로우 요소 | 개념 | 선택 기준 |
|---------------|------|----------|
| **전문 에이전트** | 특정 영역에 집중하는 단일 에이전트 | 깊은 맥락 유지가 품질의 핵심일 때 |
| **에이전트 그룹** | 복수 에이전트가 병렬로 독립 작업 | 다관점 분석·교차 검증이 품질을 높일 때 |
| **사람 개입 지점** | 검토/승인/선택 등 사용자 인터랙션 | 자동화할 수 없는 판단이 필요할 때 |
| **자동 검증** | 품질 게이트, 포맷 검사, 보안 체크 | 반복적 검증을 자동화할 때 |
| **재사용 모듈** | 도메인 지식, 반복 패턴을 캡슐화 | 검증된 패턴을 일관되게 적용할 때 |
| **외부 연동** | API, DB, 외부 서비스 통합 | 외부 데이터/기능이 필요할 때 |
| **동적 질문 수집** | 실행 중 사용자에게 구조화된 질문으로 정보 수집 | P4 규칙 적용. 선택지가 사전 정의 불가능하고 동적 판단이 필요할 때 |
| **작업 할당·추적** | 에이전트 그룹 사용 시 Task 생성·할당·의존성·진행 추적 | SOT를 대체하지 않음. 에이전트 간 작업 조율이 필요할 때 |

> **에이전트 선택의 유일한 기준은 "어떤 구조가 최종 결과물의 품질을 가장 높이는가"이다.**
> 병렬 처리가 빠르다는 이유로 에이전트 그룹을 선택하지 않는다.
> 토큰을 적게 쓴다는 이유로 단일 에이전트를 선택하지 않는다.

#### 전문 에이전트 vs 에이전트 그룹 — 품질 판단 매트릭스

5개 품질 요인으로 구조를 결정한다. "빠르니까" "싸니까"는 판단 기준이 아니다:

| 품질 요인 | 전문 에이전트 우위 | 에이전트 그룹 우위 | 판단 질문 |
|----------|-----------------|-----------------|----------|
| **맥락 깊이** | 선행 단계 결과를 깊이 참조해야 할 때 | 각 작업이 독립적 전문성을 요구할 때 | "이전 단계의 뉘앙스를 잃으면 품질이 떨어지는가?" |
| **교차 검증** | 단일 관점이 일관성을 보장할 때 | 다관점 분석이 편향을 제거할 때 | "다른 시각이 결과의 신뢰도를 높이는가?" |
| **산출물 일관성** | 문체/톤의 통일이 중요할 때 | 각 산출물이 독립적으로 완결될 때 | "산출물 간 톤 불일치가 품질 문제인가?" |
| **에러 격리** | 전체 맥락에서 에러를 잡아야 할 때 | 개별 작업 실패가 다른 작업에 영향 없어야 할 때 | "하나의 실패가 전체를 오염시키는가?" |
| **정보 전달 손실** | 파일 전달 시 뉘앙스 유실 위험이 클 때 | 구조화된 데이터만 전달해도 충분할 때 | "맥락 요약으로 전달하면 정보 손실이 발생하는가?" |

**판단 규칙:**
1. 5개 요인 중 전문 에이전트 우위가 3개 이상이면 → **전문 에이전트**
2. 에이전트 그룹 우위가 3개 이상이면 → **에이전트 그룹**
3. 동점(2:2 + 판단 불가 1개)이면 → **맥락 깊이** 요인이 tiebreaker (맥락 유지가 일반적으로 더 안전)
4. 확신이 없으면 → **전문 에이전트** (안전한 기본값 — 맥락 유지 보장)

#### 모델 수준 선택 — 품질 기반 판단

| 모델 수준 | 선택 기준 | 적합 작업 |
|----------|----------|----------|
| **최고 수준** | 핵심 작업 — 최종 품질에 직접 영향 | 핵심 분석, 최종 글쓰기, 전략 판단, 코드 아키텍처 |
| **안정 수준** | 반복 작업 — 패턴이 확립된 작업 | 데이터 수집, 포맷 변환, 표준화된 분류 |
| **보조 수준** | 단순 작업 — 판단이 최소인 작업 | 포맷 검증, 간단한 필터링, 라벨 추출 |

**판단 절차:**
1. 해당 작업이 최종 결과물의 품질에 얼마나 직접적으로 영향을 미치는가?
2. 모델 수준 간 품질 차이가 유의미한가?
   - 유의미하면 → 상위 모델
   - 유의미하지 않으면 → 하위 모델 허용
3. 확신이 없으면 → **상위 모델** (품질 보장 원칙 — 절대 기준 1)

### 5.1 Autopilot Mode

워크플로우 실행 시 **사람 개입 지점(human-in-the-loop)**을 자동 승인하여 무중단 실행하는 모드.

**핵심 원칙:**
- Autopilot은 사람 개입 지점의 **자동 승인**만 수행한다
- 모든 워크플로우 단계는 **완전히 실행**한다 — 단계 생략 금지
- 모든 산출물은 **완전한 품질**로 생성한다 — 축약 금지
- 자동 검증(Hook exit code 2)은 Autopilot에서도 **그대로 차단**한다

**대상 구분:**

| 메커니즘 | Autopilot 동작 | 근거 |
|---------|---------------|------|
| 사람 개입 지점 `(human)` | 자동 승인 — 품질 극대화 기본값 선택 | 사람의 판단을 AI가 대행 |
| 동적 질문 수집 | 자동 응답 — 품질 극대화 옵션 선택 | 사람의 선택을 AI가 대행 |
| 자동 검증 `(hook)` exit code 2 | **변경 없음 — 그대로 차단** | 결정론적 검증이므로 사람 판단 대행 대상 아님 |

**Anti-Pattern:**
1. Autopilot ≠ 단계 생략: 모든 단계를 순차적으로 완전히 실행한다
2. Autopilot ≠ 축약 출력: 모든 에이전트는 사람이 검토하는 것과 동일한 품질·분량의 산출물을 생성한다

**Anti-Skip Guard (런타임 검증):**

각 단계 완료 시 Orchestrator가 수행하는 결정론적 검증:
1. 산출물 파일이 SOT `outputs`에 경로로 기록되었는가
2. 해당 파일이 디스크에 존재하는가
3. 파일 크기가 최소 100 bytes 이상인가 (의미 있는 콘텐츠 보장)

> Claude Code의 Hook 시스템에서는 `_context_lib.py`의 `validate_step_output()` 함수가 이 검증을 결정론적으로 수행한다. 다른 도구에서는 동등한 파일 검증 로직을 구현한다.

**SOT 기록:**
```yaml
workflow:
  name: "my-workflow"
  current_step: 3
  status: "running"
  outputs:
    step-1: "research/raw-contents.md"
    step-2: "analysis/insights-list.md"
  autopilot:
    enabled: true
    activated_at: "ISO-8601"
    auto_approved_steps: [3, 6]
```

- `autopilot.enabled`: Boolean — Autopilot 활성화 여부
- `autopilot.auto_approved_steps`: 자동 승인된 단계 번호 목록
- `outputs`: 단계별 산출물 경로 — Anti-Skip Guard의 검증 대상
- 자동 승인 결정은 별도 로그 파일(`autopilot-logs/step-N-decision.md`)에 기록 (투명성 보장)
- Decision Log 표준 템플릿: Claude Code의 `references/autopilot-decision-template.md` 참조

**런타임 강화 (Claude Code 구현):**

| 계층 | 메커니즘 | 강화 내용 |
|------|---------|----------|
| **Hook** | SessionStart 컨텍스트 주입 | 세션 시작/복원 시 Autopilot 실행 규칙 + 이전 단계 검증 결과를 프롬프트에 주입 |
| **Hook** | 스냅샷 Autopilot 섹션 | 세션 경계에서 Autopilot 상태를 IMMORTAL 우선순위로 보존 |
| **Hook** | Stop Decision Log 안전망 | 자동 승인 패턴 감지 → Decision Log 누락 시 보완 생성 |
| **Hook** | PostToolUse 진행 추적 | work_log에 `autopilot_step` 필드로 단계 진행 기록 |
| **프롬프트** | Execution Checklist | 아래 정의된 각 단계 시작/실행/완료 필수 행동 목록 (Claude Code 상세: `docs/protocols/autopilot-execution.md`) |

> Hook 계층은 SOT를 **읽기 전용**으로만 접근한다 (절대 기준 2 준수).

**Autopilot Execution Checklist (도구 공통):**

모든 도구에서 Autopilot 모드로 워크플로우를 실행할 때 각 단계마다 수행해야 하는 필수 행동:

| 시점 | 필수 행동 |
|------|----------|
| **단계 시작 전** | SOT `current_step` 확인, 이전 단계 산출물 파일 존재 + 비어있지 않음 검증, `Verification` 기준 읽기 |
| **단계 실행 중** | 모든 작업 완전 실행 (축약 금지 — 절대 기준 1), 완전한 품질의 산출물 생성 |
| **단계 완료 후** | 산출물 디스크 저장, `Verification` 기준 대비 자기 검증, 실패 시 해당 부분만 재실행(최대 10회, ULW 활성 시 15회 — §5.1.1), SOT `outputs`에 경로 기록, `current_step` +1, Decision Log 생성 |
| **절대 금지** | `current_step` 2이상 한 번에 증가, 산출물 없이 진행, "자동이니까 간략하게" 축약, Verification FAIL인 채로 진행 |

> **Claude Code 상세**: `docs/protocols/autopilot-execution.md`에 `(team)` 단계, 번역, Hook 연동 등 Claude Code 전용 체크리스트가 추가로 정의되어 있다.

**활성화:** 기본값은 비활성(interactive). 워크플로우 Overview에 `Autopilot: enabled` 명시 또는 실행 시 사용자 지시로 활성화. 실행 중 토글 가능.

### 5.1.1 ULW Mode (Claude Code)

**ULW(Ultrawork)**는 Autopilot과 **직교하는 철저함 강도(thoroughness intensity) 오버레이**이다. 프롬프트에 `ulw`를 포함하면 활성화된다.

- **Autopilot** = 자동화 축(HOW) — `(human)` 승인 건너뛰기
- **ULW** = 철저함 축(HOW THOROUGHLY) — 빠짐없이, 에러 해결까지 완벽 수행

**2x2 매트릭스:**

|  | **ULW OFF** | **ULW ON** |
|---|---|---|
| **Autopilot OFF** | 표준 대화형 | 대화형 + Sisyphus Persistence(3회) + 필수 태스크 분해 |
| **Autopilot ON** | 표준 자동 워크플로우 | 자동 워크플로우 + Sisyphus 강화(재시도 3회) + 팀 철저함 |

**3가지 강화 규칙 (Intensifiers):**
1. **I-1. Sisyphus Persistence** — 최대 3회 재시도, 각 시도는 다른 접근법. 100% 완료 또는 불가 사유 보고
2. **I-2. Mandatory Task Decomposition** — TaskCreate → TaskUpdate → TaskList 필수
3. **I-3. Bounded Retry Escalation** — 동일 대상 3회 초과 재시도 금지(품질 게이트는 별도 예산 적용), 초과 시 사용자 에스컬레이션

**결정론적 강화:** Python Hook이 3개 강화 규칙의 준수를 결정론적으로 검증 (Compliance Guard). 위반 시 스냅샷 IMMORTAL 섹션에 경고 기록.

> **결합 규칙**: ULW는 Autopilot을 **강화**한다 — Autopilot의 품질 게이트 재시도 한도를 10→15회로 상향. Safety Hook 차단은 항상 존중.

상세: `docs/protocols/ulw-mode.md`

### 5.2 English-First 실행 및 번역 프로토콜

워크플로우 **실행** 시 모든 에이전트는 **영어로 작업**하고 **영어로 산출물**을 생성한다. AI는 영어에서 가장 높은 성능을 발휘하므로, 영어 우선 실행은 **절대 기준 1(품질)**의 직접적 구현이다.

#### 언어 경계

| 활동 | 언어 | 근거 |
|------|------|------|
| 워크플로우 설계 (workflow-generator 스킬) | 한국어 | 사용자와의 대화 |
| 에이전트 정의 (`.claude/agents/*.md`) | 영어 | 에이전트 프롬프트 품질 극대화 |
| 워크플로우 실행 (에이전트 작업) | **영어** | AI 성능 극대화 |
| 산출물 번역 | 영어→한국어 | `@translator` 전문 서브에이전트 |
| SOT 기록 | 언어 무관 | 경로·숫자 등 구조적 데이터 |

> **설계 문서(`workflow.md`)는 한국어 유지**. 사용자가 읽고 검토하는 설계도이므로 사용자 언어를 사용한다. 언어 전환은 **설계→실행** 경계에서 발생한다.

#### 번역 대상 판별

모든 단계가 번역을 필요로 하지 않는다:

| 산출물 유형 | 번역 여부 | 예시 |
|-----------|---------|------|
| 텍스트 콘텐츠 (분석, 보고서, 요약) | **번역** | `.md`, `.txt` |
| 코드 파일 | 번역하지 않음 | `.py`, `.js`, `.ts` |
| 데이터 파일 | 번역하지 않음 | `.json`, `.csv` |
| 설정 파일 | 번역하지 않음 | `.yaml` config, `.env` |

워크플로우 설계 시 각 단계에 `Translation: @translator` 또는 `Translation: none`을 명시하여 번역 적용 여부를 결정한다.

#### 번역 실행 프로토콜

**서브에이전트 선택 근거**: 번역은 용어 일관성과 맥락 누적이 품질의 핵심이므로, **전문 에이전트(Sub-agent)**가 에이전트 그룹보다 품질 우위 (§5 품질 매트릭스의 "맥락 깊이" + "산출물 일관성" 요인).

**실행 순서**:

```
Step N 영어 산출물 완성
  → SOT outputs.step-N 기록 + Anti-Skip Guard 검증
  → @translator 서브에이전트 호출 (Translation: @translator인 단계만)
    ① translations/glossary.yaml 읽기 (용어 사전 — RLM 외부 지속 상태)
    ② 영어 원본 전체 읽기
    ③ 확립된 용어 사용하여 완전 번역 (축약 금지 — 절대 기준 1)
    ④ 자기 검토: 원문 대조, 용어 일관성 확인
    ⑤ glossary.yaml 갱신 (새 용어 추가)
    ⑥ *.ko.md 파일 생성
  → SOT outputs.step-N-ko 기록
  → 번역 파일 존재 + 비어있지 않음 확인
  → P1 검증: python3 .claude/hooks/scripts/validate_translation.py --step N --project-dir . --check-pacs --check-sequence
  → Step N+1로 진행
```

#### 용어 사전 (Terminology Glossary)

`translations/glossary.yaml`은 번역 에이전트의 **지속적 외부 메모리**이다 (RLM 패턴). `memory: project`(ADR-051)와 함께 2계층 메모리를 구성한다: glossary.yaml = 명시적 용어 매핑, persistent memory = 암시적 문체·어투 패턴 축적.

```yaml
# translations/glossary.yaml
terms:
  "Single Source of Truth": "단일 소스 오브 트루스(Single Source of Truth)"
  "Anti-Skip Guard": "Anti-Skip Guard"  # 영어 유지
  "workflow step": "워크플로우 단계"
```

**아키텍처 정합성**:
- glossary는 **SOT가 아님** — 번역 에이전트의 로컬 작업 파일
- Orchestrator가 관리하지 않음 — 번역 에이전트가 자체 관리
- 동시 쓰기 위험 없음 — 번역은 순차 실행 (각 단계 완료 후 1회)
- 계층적 메모리: glossary.yaml(명시적 용어 사전) + `memory: project`(암시적 경험 축적) 2계층 (ADR-051)

#### SOT 기록 규칙

```yaml
outputs:
  step-1: "research/raw-contents.md"          # 영어 원본
  step-1-ko: "research/raw-contents.ko.md"    # 한국어 번역
  step-2: "data/processed.json"               # 번역 불필요 → -ko 없음
  step-3: "analysis/report.md"
  step-3-ko: "analysis/report.ko.md"
```

- `step-N-ko` 키는 접미사 규칙: Anti-Skip Guard의 `.isdigit()` 가드에 의해 자동으로 건너뛰어짐
- Anti-Skip Guard는 `step-N`(영어 원본)만 검증 → 번역 검증은 Orchestrator 체크리스트에서 수행
- 번역이 없는 단계는 `-ko` 키가 생성되지 않음

#### `(team)` 단계 번역

에이전트 그룹 단계에서의 번역 대상은 **SOT `outputs.step-N`에 기록된 공식 산출물만**:

1. Team Lead가 모든 Teammate 산출물 병합
2. SOT `outputs.step-N` 기록 + Anti-Skip Guard 검증
3. Team Lead가 `@translator` 호출 (병합된 공식 산출물에 대해)
4. SOT `outputs.step-N-ko` 기록

> Teammate의 개별 산출물은 중간 작업물(SOT 미기록)이므로 번역하지 않는다.

#### 독립 번역 검증 (선택적 — 최종 납품물용)

기본값은 번역 에이전트의 **자기 검토**로 충분하다. 최종 납품물 등 품질이 특히 중요한 단계에서는 독립 검증 서브에이전트를 추가할 수 있다:

```
@translator → output.ko.md
  → @translation-verifier (별도 서브에이전트)
    ① 영어 원본과 한국어 번역 동시 읽기
    ② 정확성, 완전성, 용어 일관성, 자연스러움 검증
    ③ Pass/Fail 판정 + 피드백
  → Fail 시: @translator에게 피드백과 함께 재번역 요청
```

이 패턴은 워크플로우 설계 시 선택적으로 적용한다.

### 5.3 Verification Protocol (작업 검증)

워크플로우 각 단계의 산출물이 **기능적 목표를 100% 달성했는지** 검증하는 프로토콜.

**핵심 원칙:**
> **"완료의 정의를 먼저 선언하고, 실행 후 검증하고, 실패 시 재실행한다."**

Anti-Skip Guard(파일 존재 + 100 bytes 이상)가 **물리적 존재**를 보장하고, Verification Protocol이 **내용적 완전성**을 보장한다. 두 계층은 독립적으로 동작하며, 둘 다 통과해야 다음 단계로 진행한다.

```
품질 보장 계층 구조:

  Anti-Skip Guard (Hook — 결정론적)
    "파일이 존재하고, 의미 있는 크기인가?"
      ↓ PASS
  Verification Gate (Agent — 의미론적)
    "기능적 목표를 100% 달성했는가?"
      ↓ PASS
  SOT 갱신 + 다음 단계 진행
```

#### 검증 기준 선언

워크플로우의 각 단계에 `Verification` 필드를 정의한다. **Task보다 앞에 배치**하여 에이전트가 "무엇이 완료인지"를 먼저 인식한 상태에서 작업을 시작한다.

```markdown
### N. [Step Name]
- **Verification**:
  - [ ] [구체적, 측정 가능한 기준]
  - [ ] [구체적, 측정 가능한 기준]
- **Task**: [작업 설명]
```

#### 검증 기준 유형 (5가지)

| 유형 | 검증 대상 | Good 예시 | Bad 예시 |
|------|---------|----------|---------|
| **구조적 완전성** | 산출물 내부 구조 | "5개 섹션(Intro, Analysis, Comparison, Recommendation, References) 모두 포함" | "잘 구성됨" |
| **기능적 목표** | 작업 목표 달성 | "각 경쟁사 가격 데이터에 3개 이상 tier + 정확한 금액 포함" | "가격 정보 있음" |
| **데이터 정합성** | 데이터 정확성 | "모든 URL이 유효하며 placeholder/example.com 없음" | "링크 확인" |
| **파이프라인 연결** | 다음 단계 입력 호환 | "Step 4 분석 에이전트가 필요로 하는 competitor_name, pricing_tiers, feature_list 필드 포함" | "다음 단계 호환" |
| **교차 단계 추적성** | 이전 단계 데이터 논리적 도출 | "분석 주장의 80% 이상이 [trace:step-N] 마커로 출처 추적 가능" | "데이터 기반" |

> **기준 작성 규칙**: 각 기준은 **제3자가 기계적으로 참/거짓 판정 가능**해야 한다. 주관적 판단("좋은 품질", "충분한 깊이")은 기준으로 사용하지 않는다. 주관적 품질 판단은 기존 `(human)` 체크포인트가 담당한다.

#### Domain Knowledge Structure (DKS)

도메인 특화 추론의 타당성 검증 패턴. Research 단계에서 `domain-knowledge.yaml`을 구축하고, Implementation 단계에서 검증 기준으로 활용. 선택적 — 모든 도메인이 필요로 하지 않음. 검증 스크립트: `validate_domain_knowledge.py` (DK1-DK7).

**DKS 필요성 판단 기준**:

| 도메인 | DKS 필요성 | 이유 |
|--------|-----------|------|
| 의학/임상, 법률 | 높음 | 도메인 특화 추론(증상→질병, 판례→원칙)의 타당성 검증 필요 |
| 경쟁 분석, 시장 조사 | 보통 | 엔터티 간 관계(지배, 경쟁) 구조화 시 품질 향상 |
| 블로그/콘텐츠, 코드 생성 | 낮음 | 타입 시스템/테스트가 대체하거나 도메인 추론 불필요 |

#### 실행 프로토콜

```
1. 검증 기준 읽기 — 에이전트가 "100% 완료"의 정의를 먼저 인식
2. 단계 실행 — 완전한 품질로 산출물 생성 (절대 기준 1)
3. Anti-Skip Guard — 파일 존재 + ≥ 100 bytes (결정론적)
4. Verification Gate — 산출물을 각 기준 대비 자기 검증 (의미론적)
   ├─ 모든 기준 PASS → verification-logs/step-N-verify.md 생성 → SOT 갱신 → 진행
   └─ 1개라도 FAIL:
       ├─ 실패 원인 식별 + 해당 부분만 재실행 (전체 재작업 아님)
       ├─ 재검증 (최대 10회 재시도)
       └─ 10회 후에도 FAIL → 사용자에게 에스컬레이션
5. SOT 갱신 — outputs 기록, current_step +1
```

> **자기 검증(Self-Verification)의 적용 범위**: 이 프로토콜의 검증은 **완전성(completeness)** 확인이다 — "실행해야 할 것을 실행했는가?" 주관적 **품질 판단(quality judgment)**은 기존 `(human)` 체크포인트가 담당하며, Verification Protocol이 이를 대체하지 않는다.

#### 검증 로그 형식

`verification-logs/step-N-verify.md`에 기록한다:

```markdown
# Verification Report — Step {N}: {Step Name}

## Criteria Check
| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | [기준 텍스트] | PASS | [산출물에서 확인한 구체적 근거] |
| 2 | [기준 텍스트] | FAIL→PASS | [1차 실패 사유] → [재실행 후 근거] |

## Result: PASS (retry: 1)
## Verified Output: research/insights.md (2,847 bytes)
```

#### (team) 단계 3계층 검증

에이전트 그룹 단계에서는 3계층 검증을 수행한다:

| 계층 | 수행자 | 검증 대상 | SOT 쓰기 |
|------|--------|---------|---------|
| **L1** | Teammate (자기 검증) | 자기 Task의 검증 기준 | **없음** — 세션 내부 완결 |
| **L1.5** | Teammate (pACS) | 자기 Task 산출물의 신뢰도 | **없음** — 점수를 보고 메시지에 포함 |
| **L2** | Team Lead (종합 검증 + 단계 pACS) | 단계 전체의 검증 기준 | **있음** — SOT outputs + pacs 갱신 |

```
Teammate: Task 실행 → 자기 검증(L1) → pACS 자기 채점(L1.5)
            → PASS + GREEN/YELLOW 시 Team Lead에 보고 (pACS 점수 포함)
            → FAIL 또는 RED 시 자체 수정 후 재검증·재채점

Team Lead: Teammate 산출물 + pACS 점수 수신
            → 단계 기준 대비 종합 검증(L2)
            → 단계 pACS = min(각 Teammate pACS) — min-score 원칙 적용
            → PASS 시 SOT 갱신 (outputs + pacs)
            → FAIL 시 SendMessage로 구체적 피드백 + 재실행 지시
```

> **SOT 호환성**: Teammate는 여전히 산출물 파일만 생성하고, SOT에 쓰지 않는다. 자기 검증과 pACS 자기 채점은 Teammate의 세션 내부에서 완결되며, 보고 메시지를 통해 Team Lead에 전달된다 (절대 기준 2 준수). Team Lead만 `pacs-logs/`에 기록하고 SOT를 갱신한다.

#### 하위 호환성

| 상황 | 동작 |
|------|------|
| `Verification` 필드 **있음** | Verification Gate 활성 — 기준 대비 검증 후 진행 |
| `Verification` 필드 **없음** | 기존 동작 유지 — Anti-Skip Guard만으로 진행 |

새로운 워크플로우 생성 시에는 `Verification` 필드를 필수로 포함한다. 기존 워크플로우는 점진적으로 추가 가능하다.

#### SOT 영향

**없음.** Verification Protocol은 에이전트 실행 프로토콜(프롬프트 계층)이며, SOT 구조를 변경하지 않는다. `current_step` 진행이 이미 검증 완료를 암묵적으로 의미하며, 검증 상세는 `verification-logs/` 파일에 기록한다.

### 5.4 pACS — predicted Agent Confidence Score (자체 신뢰 평가)

워크플로우 실행 중 에이전트가 **자기 산출물의 신뢰도를 구조적으로 자기 평가**하는 프로토콜. AlphaFold의 pLDDT(predicted Local Distance Difference Test)에서 영감을 받았다.

**핵심 원칙:**
> **"점수를 매기기 전에, 약점을 먼저 말하라."** (Pre-mortem Protocol)

Verification Protocol(§5.3)이 "완전성(completeness)" — 실행해야 할 것을 실행했는가 — 를 검증한다면, pACS는 **"신뢰도(confidence)" — 실행 결과를 얼마나 믿을 수 있는가**를 수치화한다. 두 프로토콜은 서로 다른 차원에서 품질을 보장하며 독립적으로 동작한다.

#### 3개 평가 차원 (Orthogonal Dimensions)

| 차원 | 측정 대상 | 낮은 점수 징후 |
|------|---------|-------------|
| **F — Factual Grounding** | 사실 근거의 견고함 | 출처 불명, 기억 기반 추론, 미검증 가정 |
| **C — Completeness** | 요구사항 대비 누락 없음 | 일부 항목 생략, 분석 깊이 부족 |
| **L — Logical Coherence** | 논증·구조의 내적 일관성 | 모순, 비약, 근거와 결론 불일치 |

> **3차원으로 제한하는 이유**: 에이전트의 자기 평가는 캘리브레이션 데이터가 없는 주관적 추정이다. 차원이 많을수록 정밀도 환상(precision illusion)이 커지고, 차원 간 교란이 증가한다. 3개 직교 차원이 실용적 상한이다.

#### Min-Score 원칙

> **pACS = min(F, C, L)**

가중 평균을 사용하지 않는다. 하나의 차원이 낮으면 전체 신뢰도가 낮다. 가장 약한 고리가 전체 품질을 결정한다.

#### Pre-mortem Protocol (필수 — 점수 매기기 전에 수행)

점수 인플레이션을 구조적으로 방지하는 메커니즘이다. 에이전트는 점수를 매기기 **전에** 아래 3개 질문에 반드시 답한다:

1. **"이 산출물에서 가장 불확실한 부분은 어디인가?"** — 출처 미확인, 최신성 불명, 추정에 의존하는 영역
2. **"빠뜨렸을 가능성이 가장 높은 것은 무엇인가?"** — 요구사항 일부 미충족, 엣지 케이스 미고려, 데이터 공백
3. **"이 논증에서 가장 약한 연결은 어디인가?"** — 근거→결론 비약, 전제 검증 부족, 대안 미탐색

Pre-mortem 응답에서 심각한 문제가 드러나면, 해당 차원에 높은 점수를 부여할 수 없다.

#### 행동 트리거 (Action Triggers)

| 등급 | 점수 범위 | 행동 | 근거 |
|------|---------|------|------|
| **GREEN** | pACS ≥ 70 | 자동 진행 | 에이전트가 높은 확신 — 정상 품질 |
| **YELLOW** | 50 ≤ pACS < 70 | 진행하되 약점 플래그 | 부분적 불확실성 — 사후 검토 대상 |
| **RED** | pACS < 50 | 재작업 또는 에스컬레이션 | 신뢰 불가 — 해당 부분 재실행 필수 |

#### 품질 보장 계층 구조 (4계층)

```
L0  Anti-Skip Guard (Hook — 결정론적)
      "파일이 존재하고, 의미 있는 크기인가?"
        ↓ PASS
L1  Verification Gate (Agent — 의미론적)
      "기능적 목표를 100% 달성했는가?"
        ↓ PASS
L1.5  pACS Self-Rating (Agent — 신뢰도)
        Pre-mortem → F, C, L 채점 → min(F,C,L) = pACS
        ↓ GREEN/YELLOW: 진행 (YELLOW은 플래그)
        ↓ RED: 재작업 또는 에스컬레이션
L2    Adversarial Review (Enhanced — Review: 필드 지정 단계)
        @reviewer/@fact-checker가 산출물을 독립적으로 적대적 검토 (§5.5)
```

> **L1과 L1.5의 관계**: Verification Gate는 "체크리스트 항목 PASS/FAIL" — 이진 판정. pACS는 "전체적 신뢰도 0-100" — 연속적 자기 평가. Verification이 모두 PASS여도 pACS가 낮을 수 있다 (예: 모든 항목을 다뤘지만 출처 품질이 낮은 경우).

#### SOT 기록

```yaml
workflow:
  # ... 기존 필드 ...
  pacs:
    current_step_score: 72          # 현재 단계 pACS
    dimensions: {F: 72, C: 85, L: 78}
    weak_dimension: "F"             # min-score 차원
    pre_mortem_flag: "Step 3 데이터 출처 2건 미확인"
    history:                        # 단계별 이력
      step-1: {score: 85, weak: "C"}
      step-2: {score: 72, weak: "F"}
```

- `pacs` 필드는 기존 SOT 스키마에 **추가 전용** — 기존 `workflow`, `autopilot`, `outputs`, `active_team` 필드와 독립
- `pacs`가 없는 SOT도 정상 동작 (하위 호환)
- Hook의 `capture_sot()`가 SOT 전체를 스냅샷에 포함하므로, `pacs` 필드도 자동으로 세션 경계에서 보존됨

#### Translation pACS (번역 산출물용)

`@translator` 서브에이전트의 번역 산출물에 대한 추가 3차원:

| 차원 | 측정 대상 | 낮은 점수 징후 |
|------|---------|-------------|
| **Ft — Fidelity** | 원문 의미의 정확한 전달 | 의역 과잉, 의미 왜곡, 용어 불일치 |
| **Ct — Translation Completeness** | 원문 대비 누락 없음 | 문단/문장/각주 생략 |
| **Nt — Naturalness** | 번역체가 아닌 자연스러운 한국어 | 영어 어순 직역, 번역투 |

Translation pACS = min(Ft, Ct, Nt). 행동 트리거는 동일 (GREEN/YELLOW/RED).

> **도메인 특화 번역 — `@sermon-translator`**: 설교 워크플로우에서는 `@translator` 대신 `@sermon-translator`를 사용하며, 신학 정확도 축(**Tt — Theological Accuracy**)이 추가된 4축 체계를 적용한다. Translation pACS = min(Ft, Ct, Nt, Tt). 상세: `.claude/agents/sermon-translator.md`, `translations/theological-glossary.yaml`.

#### L2 Adversarial Review (Enhanced — Review: 필드 지정 단계)

기존 L2 Calibration을 대체하는 강화된 품질 검증 계층이다. `@reviewer`(코드/산출물 비판적 분석, 읽기 전용) 및 `@fact-checker`(외부 사실 검증, 웹 접근)가 독립적으로 산출물을 검토한다. 리뷰 결과는 P1 검증(`validate_review.py`)으로 결정론적 품질 보장된다.

워크플로우 설계 시 `Review: @reviewer` 또는 `Review: @reviewer + @fact-checker`를 명시한 단계에서 적용한다. 기본값은 자기 평가(L1.5)만.

상세: §5.5 Adversarial Review 참조.

#### pACS 로그 형식

`pacs-logs/step-N-pacs.md`에 기록한다:

```markdown
# pACS Report — Step {N}: {Step Name}

## Pre-mortem
1. **Most uncertain**: [불확실한 부분]
2. **Likely omission**: [누락 가능성]
3. **Weakest link**: [가장 약한 논증 연결]

## Scores
| Dimension | Score | Rationale |
|-----------|-------|-----------|
| F (Factual Grounding) | {0-100} | [구체적 근거] |
| C (Completeness) | {0-100} | [구체적 근거] |
| L (Logical Coherence) | {0-100} | [구체적 근거] |

## Result: pACS = {min(F,C,L)} → {GREEN|YELLOW|RED}
## Weak Dimension: {F|C|L} — {약점 설명}
```

#### Autopilot에서의 pACS

- pACS GREEN → 자동 진행
- pACS YELLOW → 자동 진행 + Decision Log에 약점 차원 기록
- pACS RED → 자동 재작업 (최대 10회). 재작업 후에도 RED → 사용자 에스컬레이션
- Autopilot Decision Log에 `pacs_score`, `weak_dimension` 필드 추가

#### 하위 호환성

| 상황 | 동작 |
|------|------|
| 워크플로우에 pACS 참조 없음 | 기존 L0+L1만으로 진행 |
| SOT에 `pacs` 필드 없음 | 정상 동작 — Hook·에이전트 모두 무시 |
| Verification 없이 pACS만 | 허용하지 않음 — pACS는 Verification Gate 통과 후 수행 |

> **설계 결정**: pACS를 Verification 없이 단독 사용하는 것은 금지한다. 완전성 검증(L1) 없이 신뢰도 평가(L1.5)만 하면, "다 빠뜨렸지만 확신은 높다"는 모순적 상태가 가능해진다.

### 5.5 Adversarial Review (Enhanced L2 — 적대적 검토)

기존 L2 Calibration을 대체하는 강화된 품질 검증 계층. Generator-Critic 패턴으로 산출물을 독립적으로 검토한다.

#### 품질 계층 아키텍처

```
L0   Anti-Skip Guard (Hook — deterministic)
L1   Verification Gate (Agent self-check)
L1.5 pACS Self-Rating (Agent confidence)
L2   Adversarial Review (Enhanced L2) ← 이 섹션
       ├── Content critical analysis (LLM — @reviewer / @fact-checker)
       ├── Independent pACS scoring (LLM → Python validates)
       └── P1 deterministic validation (Python — validate_review.py)
```

#### 에이전트 정의

| 에이전트 | 도구 | 역할 | 모델 |
|---------|------|------|------|
| `@reviewer` | Read, Glob, Grep (읽기 전용) | 코드/산출물의 비판적 분석 — 결함, 논리 허점, 완전성 검토 | opus |
| `@fact-checker` | Read, Glob, Grep, WebSearch, WebFetch | 사실 검증 — 독립 소스 대비 claim-by-claim 확인 | opus |

- **도구 분리 근거 (P2)**: `@reviewer`는 코드/문서의 내부 논리를 검토하므로 읽기만 필요. `@fact-checker`는 외부 사실 검증이 필요하므로 웹 접근이 필요. 최소 권한 원칙.
- **Sub-agent 선택 근거**: 단일 리뷰어 = Sub-agent (동기적 피드백 루프). 리뷰 결과를 즉시 반영해야 하므로 Agent Team 비동기 패턴보다 효율적.

#### 실행 프로토콜

1. Generator가 산출물 생성 → L0/L1/L1.5 통과
2. Orchestrator가 `Review:` 필드에 지정된 에이전트를 Sub-agent로 호출
3. 리뷰 에이전트가 검토 보고서 생성 (stdout으로 반환)
4. Orchestrator가 `review-logs/step-N-review.md`에 보고서 저장
5. P1 검증: `python3 .claude/hooks/scripts/validate_review.py --step N --project-dir .`
6. Verdict 기반 진행:

```
PASS → Translation (있는 경우) → SOT update → 다음 단계
FAIL → Rework (최대 10회) → Re-review
       ↓ 10회 초과
       사용자 에스컬레이션
```

#### Review 필드 문법

워크플로우에서 각 단계에 `Review:` 속성으로 지정:

```markdown
### Step 3: Analysis Report (agent)
- Agent: @analyst
- Review: @reviewer          ← 코드/산출물 리뷰
- Translation: @translator
- Verification:
  - [ ] ...
```

| Review 값 | 동작 |
|-----------|------|
| `@reviewer` | 코드/산출물 비판적 분석 |
| `@fact-checker` | 사실 검증 (외부 소스 대비) |
| `@reviewer + @fact-checker` | 양쪽 모두 실행 (고위험 단계) |
| `none` 또는 미지정 | 리뷰 건너뜀 (L1.5까지만) |

#### Rubber-stamp 방지 (4계층 방어)

| 방어 계층 | 메커니즘 |
|----------|---------|
| 1. Adversarial Persona | 에이전트 정의에 "critic, not validator" 정체성 내장 |
| 2. Pre-mortem | 분석 전 3가지 실패 가설 작성 필수 — 확인 편향 방지 |
| 3. Minimum 1 Issue | P1 검증이 이슈 0건 리뷰를 자동 거부 (R5 체크) |
| 4. Independent pACS | 리뷰어 독립 채점 → Generator와 비교 (Delta ≥ 15 → 중재) |

#### P1 할루시네이션 봉쇄

리뷰 시스템에서 100% 정확해야 하는 5가지 작업을 Python 코드로 강제:

| 검증 | 함수 | 위치 |
|------|------|------|
| R1: 리뷰 파일 존재 | `validate_review_output()` | `_context_lib.py` |
| R2: 최소 크기 (100 bytes) | `validate_review_output()` | `_context_lib.py` |
| R3: 필수 섹션 4개 존재 | `validate_review_output()` | `_context_lib.py` |
| R4: PASS/FAIL 명시적 추출 | `parse_review_verdict()` | `_context_lib.py` |
| R5: 이슈 테이블 ≥ 1행 | `validate_review_output()` | `_context_lib.py` |
| pACS Delta 계산 | `calculate_pacs_delta()` | `_context_lib.py` |
| Review→Translation 순서 | `validate_review_sequence()` | `_context_lib.py` |

독립 실행 스크립트: `python3 .claude/hooks/scripts/validate_review.py --step N --project-dir .`
출력: JSON `{"valid": true, "verdict": "PASS", "critical_count": 0, ...}`

#### Translation P1 할루시네이션 봉쇄

번역 산출물에서 100% 정확해야 하는 9가지 작업을 Python 코드로 강제:

| 검증 | 함수 | 위치 |
|------|------|------|
| T1: 번역 파일 존재 | `validate_translation_output()` | `_context_lib.py` |
| T2: 최소 크기 (100 bytes) | `validate_translation_output()` | `_context_lib.py` |
| T3: 영어 원본 존재 | `validate_translation_output()` | `_context_lib.py` |
| T4: .ko.md 확장자 | `validate_translation_output()` | `_context_lib.py` |
| T5: 비-공백 콘텐츠 | `validate_translation_output()` | `_context_lib.py` |
| T6: 헤딩 수 ±20% | `validate_translation_output()` | `_context_lib.py` |
| T7: 코드 블록 수 일치 | `validate_translation_output()` | `_context_lib.py` |
| T8: glossary 타임스탬프 신선도 | `check_glossary_freshness()` | `_context_lib.py` |
| T9: pACS min() 산술 정확성 (범용) | `verify_pacs_arithmetic()` | `_context_lib.py` |

독립 실행 스크립트: `python3 .claude/hooks/scripts/validate_translation.py --step N --project-dir . --check-pacs --check-sequence`
출력: JSON `{"valid": true, "checks": {"T1": true, ...}, "pacs_valid": true}`

#### Verification Log P1 할루시네이션 봉쇄

검증 로그 구조적 무결성을 3항목으로 Python 코드로 강제:

| 검증 | 함수 | 위치 |
|------|------|------|
| V1a: 검증 로그 파일 존재 | `validate_verification_log()` | `_context_lib.py` |
| V1b: 기준별 PASS/FAIL 명시 | `validate_verification_log()` | `_context_lib.py` |
| V1c: 논리적 일관성 (FAIL 있으면 전체 PASS 불가) | `validate_verification_log()` | `_context_lib.py` |

독립 실행 스크립트: `python3 .claude/hooks/scripts/validate_verification.py --step N --project-dir .`
출력: JSON `{"valid": true, "checks": {"V1a": true, "V1b": true, "V1c": true}}`

#### 이슈 심각도 분류

| 심각도 | 정의 | Verdict 영향 |
|--------|------|-------------|
| **Critical** | 사실 오류, 필수 콘텐츠 누락, 논리 결함, 보안 취약점 | → FAIL |
| **Warning** | 불완전한 커버리지, 약한 논증, 스타일 불일치, 경미한 부정확 | → PASS (기록) |
| **Suggestion** | 개선 기회, 대안 접근법, 가독성 향상 | → PASS (선택적) |

#### 리뷰 보고서 형식

`review-logs/step-N-review.md`에 기록:

```markdown
# Adversarial Review — Step {N}: {Step Name}
Reviewer: @{reviewer|fact-checker}

## Pre-mortem (MANDATORY — before analysis)
1. **Most likely critical flaw**: [...]
2. **Most likely factual error**: [...]
3. **Most likely logical weakness**: [...]

## Issues Found
| # | Severity | Location | Problem | Suggested Fix |
|---|----------|----------|---------|---------------|
| 1 | Critical | file:line | [...] | [...] |

## Independent pACS (Reviewer's Assessment)
| Dimension | Score | Rationale |
|-----------|-------|-----------|
| F | {0-100} | [...] |
| C | {0-100} | [...] |
| L | {0-100} | [...] |

Reviewer pACS = min(F,C,L) = {score}
Generator pACS = {score}
Delta = |Reviewer - Generator| = {N}

## Verdict: {PASS|FAIL}
```

#### Autopilot에서의 Adversarial Review

- Review PASS → 자동 진행 (Translation 포함)
- Review FAIL → 자동 재작업 (최대 10회, 초과 시 사용자 에스컬레이션)
- pACS Delta ≥ 15 → Decision Log에 기록 + 재조정 권고
- Review Decision Log: `autopilot-logs/step-N-decision.md`에 리뷰 결과 포함

#### 실행 순서 제약

```
Task → L0 → L1 → L1.5 → Review(L2) → PASS → Translation → SOT update
```

- Translation은 Review PASS 후에만 실행 (P1 `validate_review_sequence()` 강제)
- Review FAIL 상태에서 Translation 실행 금지
- Review가 미지정(`none`)인 단계는 L1.5 후 바로 Translation 가능

#### 하위 호환성

| 상황 | 동작 |
|------|------|
| 워크플로우에 `Review:` 미지정 | 기존 L0+L1+L1.5만으로 진행 |
| `review-logs/` 미존재 | 정상 동작 — P1 함수가 graceful 실패 |
| `@reviewer`/`@fact-checker` 에이전트 미정의 | Sub-agent 호출 실패 시 사용자 에스컬레이션 |

> **설계 결정**: Adversarial Review를 기존 L2 Calibration의 Enhanced 버전으로 위치시킨다. L2 Calibration의 "교차 검증"을 "적대적 검토"로 강화하되, 기존 L0/L1/L1.5 계층은 전혀 변경하지 않는다. `Review:` 필드가 없는 단계는 이전과 동일하게 동작한다.

---

### 5.6 Abductive Diagnosis Protocol

품질 게이트(Verification Gate, pACS, Adversarial Review) FAIL 시 즉시 재시도하는 대신, **3단계 진단**을 거쳐 재시도 품질을 높인다. 기존 4계층 QA(L0→L1→L1.5→L2)는 변경하지 않으며, FAIL과 재시도 **사이**에 삽입되는 부가 계층이다.

#### 3단계 프로세스

| 단계 | 주체 | 입력 | 출력 | 성격 |
|------|------|------|------|------|
| **Step A — P1 사전 증거 수집** | `diagnose_context.py` | SOT, 로그 파일, 재시도 이력 | 구조화된 증거 번들 (JSON) | 결정론적 |
| **Step B — LLM 진단** | Orchestrator (Claude) | 증거 번들 + 가설 우선순위 | 진단 로그 (`diagnosis-logs/step-N-gate-timestamp.md`) | 판단적 |
| **Step C — P1 사후 검증** | `validate_diagnosis.py` | 진단 로그 | AD1-AD10 구조적 무결성 (JSON) | 결정론적 |

#### 가설 체계 (H1/H2/H3/H4)

| 가설 | 라벨 | 우선순위 결정 기준 |
|------|------|-------------------|
| **H1** | 상류 데이터 품질 문제 | 이전 단계 산출물 누락/과소 시 최우선 |
| **H2** | 현재 단계 실행 격차 | 기본 최우선 (가장 빈번) |
| **H3** | 기준 해석 오류 | Review 게이트에서 우선순위 상승 |
| **H4** | 역량 갭 — 도구/스크립트/인프라 부재 | H2 2회 반복 미해결 시 자동 승격 |

#### Fast-Path (FP1-FP3)

LLM 진단을 건너뛰는 결정론적 단축 경로:

| ID | 조건 | 진단 | 동작 |
|----|------|------|------|
| **FP1** | 산출물 파일 부재 | "파일 미생성" | 즉시 재실행 |
| **FP2** | 산출물 크기 < 100B | "불완전 생성" | 즉시 재실행 |
| **FP3** | 동일 가설 2회 연속 선택 | "접근법 고착" | 사용자 에스컬레이션 |

#### P1 사후 검증 (AD1-AD10)

| 검증 | 설명 |
|------|------|
| AD1 | 진단 로그 파일 존재 |
| AD2 | 최소 크기 ≥ 100 bytes |
| AD3 | Gate 필드 일치 |
| AD4 | 선택된 가설 존재 (H1/H2/H3/H4) |
| AD5 | 증거 항목 ≥ 1개 |
| AD6 | Action Plan 섹션 존재 |
| AD7 | 순방향 단계 참조 금지 |
| AD8 | 가설 ≥ 2개 (대안 고려) |
| AD9 | 선택 가설이 나열된 가설 중 하나 |
| AD10 | 이전 진단 참조 (재시도 > 0 시) |

#### 하위 호환성

| 상황 | 동작 |
|------|------|
| `diagnosis-logs/` 미존재 | 기존 동작 그대로 — 진단 없이 재시도 |
| 진단 없이 재시도 실행 | 정상 동작 — 안전망이 stderr 경고만 출력 |
| Fast-Path 해당 | LLM 진단 건너뛀 — P1 사전 증거만으로 즉시 판단 |

> **설계 결정**: Abductive Diagnosis는 기존 4계층 QA를 변경하지 않는 부가 계층이다. 진단 결과는 `diagnosis-logs/`에만 기록하고 SOT는 수정하지 않는다. Knowledge Archive에 `diagnosis_patterns`로 아카이빙되어 cross-session 학습이 가능하다.

---

## 6. 스킬 체계

### workflow-generator

워크플로우 정의 파일(`workflow.md`)을 설계·생성하는 스킬.

- **트리거**: "워크플로우 만들어줘", "자동화 파이프라인 설계", "작업 흐름 정의"
- **진입점**: `.claude/skills/workflow-generator/SKILL.md`
- **두 가지 케이스**: (1) 아이디어만 있는 경우 → 대화형 질문, (2) 설명 문서가 있는 경우 → 문서 분석 우선

### doctoral-writing

박사급 학위 논문의 학문적 엄밀성과 명료성을 갖춘 글쓰기 스킬.

- **트리거**: "논문 스타일로 써줘", "학술적 글쓰기", "논문 문장 다듬기"
- **진입점**: `.claude/skills/doctoral-writing/SKILL.md`
- **핵심 원칙**: 명료성, 간결성, 학술적 엄밀성, 논리적 흐름

---

## 7. 스킬 개발 규칙

새로운 스킬을 만들거나 기존 스킬을 수정할 때:

1. **모든 절대 기준을 반드시 포함** — 해당 도메인에 맞게 맥락화하여 적용 (코드 변경이 아닌 도메인의 경우 절대 기준 3은 N/A 가능)
2. **파일 간 역할 분담** — 스킬 정의(WHY), 참조 자료(WHAT/HOW/VERIFY)
3. **절대 기준 간 충돌 시나리오를 구체적으로 명시** — 추상적 규칙이 아닌 실전 판단 기준
4. **수정 후 반드시 성찰** — 문구만 넣지 않고, 기존 내용과 충돌 여부를 점검

---

## 8. 언어 및 스타일

- **프레임워크 문서·사용자 대화**: 한국어
- **워크플로우 실행**: 영어 (AI 성능 극대화 — 절대 기준 1 근거). 상세: §5.2
- **최종 산출물**: 영어 원본 + 한국어 번역 쌍
- **기술 용어**: 영어 유지 (SOT, Agent, Orchestrator, Hooks 등)
- **시각화**: Mermaid 다이어그램 선호
- **서술 깊이**: 간략 요약보다 포괄적·데이터 기반 서술 선호
- **코드 주석**: 한국어 (프레임워크 코드) / 영어 (워크플로우 실행 코드)

---

## 9. 범용 시스템 프롬프트 체계 (Hub-and-Spoke)

이 프로젝트는 **어떤 AI CLI 도구를 사용하든** 동일한 방법론이 자동으로 적용되도록 설계되었다.

### 아키텍처

```
                AGENTS.md (Hub — 방법론 SOT)
               /    |    |    \    \     \
          CLAUDE  GEMINI .cursor  .github/
          .md     .md    /rules   copilot-
                         (Spoke)  instructions.md
```

- **Hub (AGENTS.md)**: 절대 기준, 설계 원칙, 워크플로우 구조의 유일한 정의 지점
- **Spoke (도구별 파일)**: Hub를 참조하면서 해당 도구의 고유 기능에 맞는 구현 매핑을 제공

### 도구별 파일 매핑

| AI CLI 도구 | 시스템 프롬프트 파일 | 자동 읽기 | AGENTS.md 인식 |
|------------|-------------------|----------|---------------|
| **Claude Code** | `CLAUDE.md` | Yes | 별도 파일 |
| **Gemini CLI** | `GEMINI.md` | Yes | 설정으로 추가 로드 |
| **Codex CLI** | `AGENTS.md` (직접) | Yes | 네이티브 |
| **Copilot CLI** | `.github/copilot-instructions.md` | Yes | 자동 인식 |
| **Cursor** | `.cursor/rules/agenticworkflow.mdc` | Yes (alwaysApply) | 인식 |

### Spoke 파일 원칙

1. **절대 기준 인라인 + 상세 참조**: 각 Spoke는 절대 기준의 핵심 정의(1~2문장)를 인라인으로 포함하고, 상세 내용은 `AGENTS.md §2` 참조로 위임한다.
2. **도구별 구현 매핑**: 해당 도구의 고유 기능(Hook, Agent, Plugin 등)과 AgenticWorkflow 개념의 대응을 명시한다.
3. **컨텍스트 보존 대안**: Claude Code의 Context Preservation System을 사용할 수 없는 도구에서는 해당 도구에서 가능한 대안을 안내한다.

### 충돌 해소

> **AGENTS.md의 절대 기준이 모든 Spoke보다 우선한다.** 도구 종속적 구현이 원칙과 충돌하면 원칙이 이긴다.

### 절대 기준 변경 시 동기화

AGENTS.md의 절대 기준이 변경되면, 모든 Spoke 파일의 인라인 복제도 동기화해야 한다:
- `CLAUDE.md`, `GEMINI.md` — 직접 수정
- `.cursor/rules/` — 인라인 부분 수정
- `.github/copilot-instructions.md` — 인라인 부분 수정
