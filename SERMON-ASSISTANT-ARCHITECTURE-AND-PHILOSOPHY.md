# Sermon Assistant: Architecture and Philosophy

이 문서는 **Sermon Assistant** 시스템의 **설계 철학**과 **아키텍처 전체 조감도**를 기술한다.
부모 프레임워크(AgenticWorkflow)의 방법론은 [`AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md`](AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md)를 참조한다.

> **문서 범위**: 이 문서는 설교 준비 도메인에 특화된 아키텍처만 다룬다.
> 절대 기준, SOT 패턴, 4계층 품질 보장 등 프레임워크 수준의 설계 철학은 부모 문서에 있다.

---

## 1. 설계 철학 (Design Philosophy)

### 1.1 핵심 문제: 설교 준비는 왜 어려운가

설교 준비는 단순한 글쓰기가 아니다. 최소 11개 전문 학문 분야의 교차 분석을 요구하는 **박사급 연구 작업**이다:

| 분야 | 전문성 | 난이도 |
|------|--------|--------|
| 원문 분석 | 히브리어/헬라어 형태론, 구문론, 담화 분석 | Ph.D. |
| 사본학 | 사본 전통 비교, 본문비평 장치 해설 | Ph.D. |
| 구조 분석 | 문학적 단위 구분, 교차대구, 포함구조 | M.Div.+ |
| 평행 본문 | 정경 내 상호텍스트성, 구약-신약 연결 | M.Div.+ |
| 신학적 분석 | 조직신학, 성경신학, 구속사 | Th.M.+ |
| 문학 비평 | 장르, 비유, 상징, 서사 기법 | M.Div.+ |
| 수사학 | 고대 Greco-Roman 수사학, 설득 전략 | Ph.D. |
| 역사 맥락 | 고대 근동, 제2성전기 역사 | Ph.D. |
| 핵심 단어 | 어원, 의미 발전사, 동시대 용례 | Th.M.+ |
| 성경 지리 | 고고학, 지형, 기후 | M.A.+ |
| 문화 배경 | 관습, 의례, 물질 문화, 사회 구조 | M.A.+ |

한 명의 목회자가 이 모든 분야를 매주 깊이 있게 분석하는 것은 **시간적으로 불가능**하다. 이것이 Sermon Assistant가 존재하는 이유다.

### 1.2 설계 원칙: 전문가 위임 + 할루시네이션 원천 봉쇄

설교 연구에서 AI의 가장 큰 위험은 **그럴듯하지만 틀린 정보**(할루시네이션)다. "모든 학자가 동의한다"는 문장, 존재하지 않는 사본 이문, 부정확한 히브리어 어근 분석 — 이런 오류가 설교에 그대로 반영되면 교회 전체에 잘못된 가르침이 전달된다.

Sermon Assistant의 설계 원칙은 이 위험에 대한 직접적 대응이다:

1. **전문가 위임 (P2)**: 11개 분야를 하나의 AI에게 맡기지 않고, 각 분야별 전문 에이전트에게 위임
2. **할루시네이션 봉쇄 (GRA)**: 생성 시점에서 차단(Firewall) + 교차 검증(Gate) + 통합 평가(SRCS)
3. **근거 기반 출력 (GroundedClaim)**: 모든 연구 결과는 출처·신뢰도·불확실성을 구조화하여 출력
4. **결정론적 검증 (P1)**: Python 코드로 클레임 스키마, 출처 요구사항, 방화벽 패턴을 결정론적으로 검증

### 1.3 품질 절대주의의 도메인 적용

부모(AgenticWorkflow)의 **절대 기준 1(품질)**이 설교 도메인에서 어떻게 발현되는가:

| 일반적 접근 | Sermon Assistant의 접근 | 근거 |
|-----------|----------------------|------|
| 연구 범위 축소하여 빠르게 | 11개 전문 영역 전체 분석 | 품질 > 속도 |
| AI 단독 분석으로 효율화 | 4-Wave 병렬 + 교차검증 | 품질 > 비용 |
| 신뢰도 높은 것만 출력 | 모든 클레임에 신뢰도·불확실성 명시 | 투명성 = 품질 |
| 한 번에 원고 작성 | 연구 → 메시지 도출 → 아웃라인 → 원고 | 단계적 정제 |

---

## 2. 시스템 아키텍처 (System Architecture)

### 2.1 전체 흐름

```
사용자 입력 (주제/본문/시리즈)
        │
        ▼
┌──────────────────────────────────────────────────────┐
│  Phase 0: Initialization                              │
│  session.json + todo-checklist.md + state.yaml        │
│  3-File Architecture 초기화                            │
└──────────────────────┬───────────────────────────────┘
                       │
        ▼──────────────────────────────────────────────▼
┌──────────────────────────────────────────────────────┐
│  Phase 1: Research (11개 박사급 에이전트 + GRA)         │
│                                                       │
│  Wave 1 (병렬) ──▶ Gate 1 ──▶ Wave 2 (병렬) ──▶      │
│  Gate 2 ──▶ Wave 3 (병렬) ──▶ Gate 3 ──▶             │
│  Wave 4 (순차) ──▶ SRCS 평가 ──▶ 종합                 │
│                                                       │
│  HITL-1: 본문 선정  │  HITL-2: 연구 결과 검토          │
└──────────────────────┬───────────────────────────────┘
                       │
        ▼──────────────────────────────────────────────▼
┌──────────────────────────────────────────────────────┐
│  Phase 2: Planning (설교 설계)                         │
│  스타일 선택 → 핵심 메시지 도출 → 아웃라인 설계         │
│                                                       │
│  HITL-3a: 스타일 │ HITL-3b: 메시지 │ HITL-4: 아웃라인  │
└──────────────────────┬───────────────────────────────┘
                       │
        ▼──────────────────────────────────────────────▼
┌──────────────────────────────────────────────────────┐
│  Phase 2.5: Style Analysis (조건부)                    │
│  사용자 설교 샘플 분석 → 스타일 프로파일 생성            │
└──────────────────────┬───────────────────────────────┘
                       │
        ▼──────────────────────────────────────────────▼
┌──────────────────────────────────────────────────────┐
│  Phase 3: Implementation (원고 작성)                   │
│  포맷 설정 → 초안 작성 → 품질 검토 → 최종 원고          │
│                                                       │
│  HITL-5a: 포맷  │  HITL-5b: 최종 승인                  │
└──────────────────────────────────────────────────────┘
        │
        ▼
  sermon-final.md (최종 설교 원고)
```

### 2.2 에이전트 토폴로지 (Agent Topology)

```
                    Orchestrator (sermon-orchestrator)
                    ├── SOT Writer (state.yaml)
                    ├── Session Manager (session.json)
                    └── Checklist Manager (todo-checklist.md)
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    Input Agents    Research Agents   Output Agents
    ┌──────────┐    ┌──────────────┐  ┌──────────────┐
    │ passage-  │    │ Wave 1 (4)   │  │ message-     │
    │ finder    │    │ Wave 2 (3)   │  │ synthesizer  │
    │           │    │ Wave 3 (3)   │  │ outline-     │
    │ series-   │    │ Wave 4 (1)   │  │ architect    │
    │ analyzer  │    │              │  │ sermon-writer│
    └──────────┘    │ unified-srcs │  │ sermon-      │
                    │ research-    │  │ reviewer     │
                    │ synthesizer  │  │ style-       │
                    └──────────────┘  │ analyzer     │
                                      └──────────────┘
                    Quality Agents
                    ┌──────────────┐
                    │ unified-srcs-│
                    │ evaluator    │
                    └──────────────┘
```

**에이전트 수**: 총 20개 설교 전문 에이전트 + 3개 공통 에이전트(reviewer, translator, fact-checker) = 23개

### 2.3 Wave 실행 모델

연구 에이전트 간의 의존성을 고려한 **하이브리드 병렬-순차 실행**:

```
Wave 1 (독립 분석) ─────────────────────────────────────
├─ @original-text-analyst    원문 분석 (히브리어/헬라어)
├─ @manuscript-comparator    번역본/사본 비교
├─ @biblical-geography-expert 성경지리
└─ @historical-cultural-expert 역사문화적 배경
          │
          ▼ Cross-Validation Gate 1

Wave 2 (1차 의존 분석) ── Wave 1 결과 참조 ─────────────
├─ @structure-analyst        구조 분석 ← 원문 분석
├─ @parallel-passage-analyst 평행 본문 ← 원문 분석
└─ @keyword-expert           핵심 단어 ← 원문 분석
          │
          ▼ Cross-Validation Gate 2

Wave 3 (2차 의존 분석) ── Wave 2 결과 참조 ─────────────
├─ @theological-analyst      신학적 분석 ← 구조 분석
├─ @literary-analyst         문학적 분석 ← 구조 분석
└─ @historical-context-analyst 역사/문화 맥락 ← 배경연구
          │
          ▼ Cross-Validation Gate 3

Wave 4 (통합 분석) ── Wave 3 결과 참조 ─────────────────
└─ @rhetorical-analyst       플롯/수사학 ← 문학적 분석
          │
          ▼ Full SRCS Evaluation
```

**설계 근거**: Wave 1은 본문 자체에 대한 독립적 분석이므로 병렬 실행이 안전하다. Wave 2부터는 Wave 1의 원문 분석 결과를 참조해야 하므로 Gate를 통과한 후에만 실행된다. 이 의존성 구조가 분석 품질을 보장한다.

---

## 3. GRA (Grounded Research Architecture)

Sermon Assistant의 핵심 차별점. 3계층으로 할루시네이션을 원천 차단한다.

### 3.1 Layer 1: Agent Self-Verification

각 연구 에이전트가 출력 시점에서 자체 검증:

```
에이전트 출력 생성
       │
       ▼
┌─ GroundedClaim 스키마 준수 ──────────────────────┐
│  - id: "{PREFIX}-{NNN}" 형식                      │
│  - claim_type: 6종 중 하나                        │
│  - sources: 유형별 필수 출처 충족                   │
│  - confidence: ClaimType별 최소 임계값 이상        │
│  - uncertainty: 불확실성 표현 (해당 시)             │
└──────────────────────────────────────────────────┘
       │
       ▼
┌─ Hallucination Firewall ─────────────────────────┐
│  BLOCK:          "모든 학자가 동의", "100%"        │
│  REQUIRE_SOURCE: "정확히 N개", "BC YYYY년" (단독)  │
│  SOFTEN:         "확실히", "분명히", "명백히"       │
│  VERIFY:         "전통적으로", "OO 박사가 주장"     │
└──────────────────────────────────────────────────┘
       │
       ▼
┌─ Mini-SRCS 자기 평가 ────────────────────────────┐
│  CS(Citation) + GS(Grounding) + US(Uncertainty)   │
│  + VS(Verifiability) = 4축 점수                    │
└──────────────────────────────────────────────────┘
```

### 3.2 Layer 2: Cross-Validation Gates

Wave 간 경계에서 **구조적(Python) + 의미론적(AI)** 이중 검증:

| Gate | 위치 | 구조적 검증 (코드) | 의미론적 검증 (AI) |
|------|------|-------------------|-------------------|
| Gate 1 | Wave 1→2 | 4개 파일 존재 + 클레임 스키마 | 독립 분석 간 모순 탐지 |
| Gate 2 | Wave 2→3 | 3개 파일 존재 + 의존성 참조 확인 | 원문-구조-평행 일관성 |
| Gate 3 | Wave 3→4 | 3개 파일 존재 + 의존성 참조 확인 | 신학-문학-역사 일관성 |

Gate 실패 시: 모순이 있는 에이전트를 수정 지시와 함께 재실행.

### 3.3 Layer 3: Unified SRCS Evaluation

전체 연구가 완료된 후, `@unified-srcs-evaluator`가 통합 평가:

| 축 | 이름 | 설명 | 가중치 (FACTUAL) |
|----|------|------|-----------------|
| **CS** | Citation Score | 출처 점수 | 0.3 |
| **GS** | Grounding Score | 근거 품질 점수 | 0.4 |
| **US** | Uncertainty Score | 불확실성 표현 점수 | 0.1 |
| **VS** | Verifiability Score | 검증가능성 점수 | 0.2 |

- **SRCS 임계값**: 70점 미만 → 플래그 후 사용자 검토 요청
- **Grounding Rate 임계값**: 90% 미만 → 재검증

### 3.4 GroundedClaim 스키마

모든 연구 에이전트의 출력 형식:

```yaml
claims:
  - id: "OTA-001"                    # 에이전트 접두사 + 순번
    text: "실제 클레임 문장"
    claim_type: LINGUISTIC           # 6종: FACTUAL/LINGUISTIC/HISTORICAL/THEOLOGICAL/INTERPRETIVE/APPLICATIONAL
    sources:
      - type: PRIMARY                # PRIMARY/SECONDARY/TERTIARY
        reference: "BDB, p.944-945"
        verified: true
    confidence: 98                   # 0-100
    uncertainty: null                # 불확실성 표현 또는 null
```

**ClaimType별 요구사항**:

| ClaimType | 필수 출처 유형 | 최소 출처 수 | 최소 신뢰도 |
|-----------|--------------|------------|-----------|
| FACTUAL | PRIMARY or SECONDARY | 1 | 95 |
| LINGUISTIC | PRIMARY (필수) | 1 | 90 |
| HISTORICAL | SECONDARY or TERTIARY | 1 | 80 |
| THEOLOGICAL | SECONDARY or TERTIARY | 1 | 70 |
| INTERPRETIVE | 제한 없음 | 0 | 70 |
| APPLICATIONAL | 제한 없음 | 0 | 60 |

---

## 4. External Memory Strategy (3-File Architecture)

컨텍스트 윈도우 한계를 극복하기 위한 외부 메모리 전략. 11개 연구 에이전트의 출력이 컨텍스트 윈도우를 쉽게 초과하므로, 핵심 정보를 3개 파일로 외부화한다.

```
┌─────────────────────────────────────────────────────┐
│  1. Context File: session.json                       │
│     - 프로젝트 목표/방향성                            │
│     - 입력 정보 (본문, 모드)                          │
│     - 옵션 설정                                      │
│     - HITL 스냅샷 (context_snapshots)                │
├─────────────────────────────────────────────────────┤
│  2. Todo File: todo-checklist.md                     │
│     - 155단계 체크리스트                              │
│     - 완료 표시 [x] / 미완료 [ ]                     │
│     - 마지막 작업 지점 파악용                          │
├─────────────────────────────────────────────────────┤
│  3. Insights File: research-synthesis.md             │
│     - 11개 연구 결과 압축본 (2000-2500자)             │
│     - 핵심 정보만 추출                                │
└─────────────────────────────────────────────────────┘
```

**Context Reset Model**: 컨텍스트 리셋 시 3개 파일을 로드하여 자동 복구:

| 리셋 포인트 | 로드할 파일 | 목적 |
|------------|-----------|------|
| HITL-2 후 | session.json, research-synthesis.md, checklist | Planning Phase 진입 |
| HITL-3b 후 | session.json, outline.md, synthesis, checklist | Implementation 진입 |
| HITL-5b 후 | session.json, sermon-final.md, checklist | 완료 확인 |

---

## 5. HITL (Human-In-The-Loop) 설계

설교 준비에서 목회자의 판단이 필수적인 7개 지점에 체크포인트를 배치:

```
Phase 0 ──▶ HITL-1 (본문 선정) ──▶ Phase 1 Research
                                           │
Phase 1 ──▶ HITL-2 (연구 검토) ──▶ Phase 2 Planning
                                           │
Phase 2 ──▶ HITL-3a (스타일) ──▶ HITL-3b (메시지) ──▶ HITL-4 (아웃라인)
                                           │
Phase 3 ──▶ HITL-5a (포맷) ──▶ HITL-5b (최종 승인)
```

| Checkpoint | 사용자 결정 | Context Reset Point |
|-----------|-----------|-------------------|
| HITL-1 | 본문 선택 + 원문 분석 수준 + 연구 범위 | No |
| HITL-2 | 연구 결과 검토 + 추가 연구 요청 | **Yes** |
| HITL-3a | 설교 유형 + 청중 유형 | No |
| HITL-3b | Big Idea 선택 + 강조점 조정 | **Yes** |
| HITL-4 | 아웃라인 승인/수정/재구성 | No |
| HITL-5a | 원고 형식 + 분량 + 문체 | No |
| HITL-5b | 최종 승인/수정/재작성 | **Yes** |

---

## 6. 결정론적 라이브러리 (_sermon_lib.py)

1,604줄의 Python 라이브러리. 모든 함수가 **결정론적**(AI 판단 없음)이며, P1 할루시네이션 봉쇄의 핵심 구현체.

### 6.1 함수 도메인 분류

| 도메인 | 주요 함수 | 역할 |
|--------|---------|------|
| 스키마 검증 | `validate_grounded_claim()`, `validate_sermon_sot_schema()` | GroundedClaim, SRCS, SOT 구조 검증 |
| 방화벽 | `check_hallucination_firewall()` | Regex 기반 패턴 차단 |
| SRCS 점수 | `calculate_srcs_score()` | 4축 수학적 계산 |
| Gate 검증 | `validate_gate_structure()`, `validate_gate_result()` | 교차검증 게이트 구조 검증 |
| 체크리스트 | `generate_checklist()`, `update_checklist()` | 155단계 체크리스트 관리 |
| 세션 초기화 | `initialize_sermon_output()` (P1 Master) | Phase 0 전체 설정 (디렉토리·세션·체크리스트 일괄) |
| 컨텍스트 해석 | `resolve_sermon_context()` (P1 Master) | Resume/Status 경로·상태 일괄 해석 |
| 에러 처리 | `handle_research_incomplete()`, `handle_validation_failure()` | 5종 에이전트 에러 + 3종 워크플로우 에러 |
| 에이전트 디스패치 | `build_research_agent_prompt()`, `resolve_dependency_files()` | 의존성 해결 + 프롬프트 생성 |
| 출력 검증 | `validate_agent_output()`, `extract_claims_from_output()` | P1 클레임 추출 + 통합 파이프라인 |
| Gate 완료 | `record_gate_completion()` | SOT 안전 업데이트 |

### 6.2 P1 봉쇄 지점

Orchestrator가 반드시 `_sermon_lib.py` 함수를 사용해야 하는 지점:

| 지점 | 금지 행위 | 필수 함수 |
|------|---------|---------|
| Phase 0 초기화 | 개별 함수 수동 조합 | `initialize_sermon_output()` (P1 Master) |
| 에이전트 프롬프트 생성 | 수동 프롬프트 작성 | `build_research_agent_prompt()` |
| 에이전트 출력 검증 | 수동 클레임 읽기 | `validate_agent_output()` |
| Gate 통과 판정 | AI 단독 판정 | `validate_gate_structure()` + AI + `validate_gate_result()` |
| Gate 완료 기록 | 수동 SOT 수정 | `record_gate_completion()` |
| 번역 배치 실행 | 수동 파일 매핑 | `prepare_translation_batch()` → `finalize_translation_batch()` |
| Resume/Status 경로 해석 | 수동 경로 조합 | `resolve_sermon_context()` (P1 Master) |

---

## 7. 에러 처리 아키텍처

### 7.1 에이전트 수준 (5종)

| 실패 유형 | 설명 | 처리 |
|----------|------|------|
| `LOOP_EXHAUSTED` | 3회 사고 후 미해결 | 부분 결과 수용 + 실패 지점 명시 |
| `SOURCE_UNAVAILABLE` | 필수 출처 접근 불가 | 대체 출처 탐색 → 실패 시 스킵 |
| `INPUT_INVALID` | 잘못된 입력 | 재입력 요청 |
| `CONFLICT_UNRESOLVABLE` | 모순 해결 불가 | 양쪽 견해 병기 |
| `OUT_OF_SCOPE` | 범위 이탈 | 범위 내 결과만 반환 |

### 7.2 워크플로우 수준 (3종)

| 핸들러 | 트리거 | 동작 |
|--------|--------|------|
| `on_research_incomplete` | Wave 내 에이전트 ≥50% 실패 | 부분 진행 또는 중단 |
| `on_validation_failure` | Cross-Validation Gate 실패 | 사용자 검토 요청 |
| `on_srcs_below_threshold` | SRCS < 70 | 플래그 후 검토 |

---

## 8. DNA 유전: 부모로부터 물려받은 것

Sermon Assistant는 AgenticWorkflow의 **전체 게놈**을 내장하고 있다. 아래는 유전된 DNA와 설교 도메인에서의 발현 형태:

| 부모 DNA | 설교 도메인 발현 |
|---------|----------------|
| 절대 기준 1 (품질) | 11개 전문 영역 전체 분석, 토큰 비용 무시 |
| 절대 기준 2 (SOT) | state.yaml + session.json + todo-checklist.md 계층 구조 |
| 절대 기준 3 (CCP) | _sermon_lib.py 1,604줄 결정론적 코드 |
| 4계층 품질 보장 | GRA 3-Layer + SRCS 4축 평가로 확장 |
| Context Preservation | 3-File Architecture + Context Reset Model |
| Hook 시스템 | _sermon_lib.py P1 검증 함수 + 기존 Hook 전체 상속 |
| Autopilot Mode | HITL 7개 지점의 자동 승인 지원 |
| Safety Hook | 기존 22개 Hook 스크립트 전체 동작 |

**새로 발현된 유전자** (설교 도메인 고유):
- GRA (Grounded Research Architecture) — 학술 연구의 할루시네이션 봉쇄
- GroundedClaim 스키마 — 구조화된 근거 기반 출력
- Hallucination Firewall — 설교 연구 특화 차단 패턴 (한국어/영어)
- Cross-Validation Gate — Wave 간 교차 검증
- External Memory Strategy — 대규모 연구 산출물의 컨텍스트 관리

---

## 9. 테스트 아키텍처

4계층 pytest 테스트 스위트 (216개 테스트):

| Layer | 파일 | 테스트 수 | 검증 대상 |
|-------|------|---------|---------|
| L1 Unit | `test_layer1_unit.py` | 다수 | _sermon_lib.py 개별 함수 |
| L2 E2E | `test_layer2_e2e_hooks.py` | 다수 | Hook 스크립트 종단간 동작 |
| L3 Integration | `test_layer3_integration.py` | 다수 | 컴포넌트 간 통합 |
| L4 Structural | `test_layer4_structural.py` | 다수 | 코드-문서 구조적 일관성 |

---

## 10. 설계 결정 요약

| 결정 | 대안 | 선택 이유 |
|------|------|---------|
| 11개 전문 에이전트 | 단일 범용 에이전트 | 전문성 분리 → 품질 향상 (P2) |
| 4-Wave 실행 | 전체 병렬 | 의존성 있는 분석의 순서 보장 |
| GroundedClaim | 자유 형식 | 결정론적 검증 가능 (P1) |
| 3-File Architecture | 전체 SOT | 컨텍스트 윈도우 한계 극복 |
| 12개 슬래시 커맨드 | 자동 진행 | HITL 정밀 제어 |
| Python 검증 라이브러리 | AI 판단 | 할루시네이션 봉쇄 (P1) |
| 4-Wave + Gate | 일괄 실행 | 교차 검증으로 모순 사전 탐지 |

---

## 부록: 문서 관계도

```
┌──────────────────────────────────┐
│  부모 문서 (방법론/프레임워크)      │
│  AGENTICWORKFLOW-ARCHITECTURE-   │
│  AND-PHILOSOPHY.md               │
│  AGENTICWORKFLOW-USER-MANUAL.md  │
│  soul.md                         │
│  AGENTS.md                       │
└──────────────┬───────────────────┘
               │ DNA 유전
               ▼
┌──────────────────────────────────┐
│  자식 문서 (도메인 고유)           │
│  SERMON-ASSISTANT-ARCHITECTURE-  │
│  AND-PHILOSOPHY.md (이 문서)      │
│  SERMON-ASSISTANT-USER-MANUAL.md │
│  README.md (자식 시스템 진입점)    │
└──────────────────────────────────┘
```
