# Sermon Assistant 사용자 매뉴얼

> **이 문서의 범위**: 이 매뉴얼은 **Sermon Assistant 시스템**을 사용하는 방법을 안내합니다.
> 즉, AI를 활용하여 **설교를 준비하는 방법**입니다.
>
> 이 시스템의 **기반 프레임워크(AgenticWorkflow)**의 사용법은
> [`AGENTICWORKFLOW-USER-MANUAL.md`](AGENTICWORKFLOW-USER-MANUAL.md)를 참조하세요.

| 문서 | 대상 |
|------|------|
| **이 문서 (`SERMON-ASSISTANT-USER-MANUAL.md`)** | Sermon Assistant 사용법 — 설교 준비 방법 |
| **`README.md`** | 프로젝트 첫 소개 — 개요, 빠른 시작 |
| **`SERMON-ASSISTANT-ARCHITECTURE-AND-PHILOSOPHY.md`** | 설계 철학, GRA 아키텍처, 에이전트 구조 |
| **`AGENTICWORKFLOW-USER-MANUAL.md`** | 기반 프레임워크(AgenticWorkflow) 사용법 |
| **`AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md`** | 프레임워크 설계 철학 및 아키텍처 |

---

## 1. 시작하기

### 1.1 사전 준비

| 항목 | 필수 여부 | 설명 |
|------|----------|------|
| [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) | 필수 | `npm install -g @anthropic-ai/claude-code` |
| Python 3.10+ | 필수 | GRA 검증 라이브러리 실행 |
| PyYAML | 필수 | `pip install pyyaml` |
| GitHub 계정 | 권장 | 저장소 clone |

### 1.2 설치 및 실행

```bash
git clone https://github.com/idoforgod/Sermon-Assistant-AgenticWorkflow.git
cd Sermon-Assistant-AgenticWorkflow
claude          # Claude Code 실행
```

Claude Code가 실행되면 `CLAUDE.md`를 자동으로 읽고, 시스템의 절대 기준·GRA 프로토콜·22개 Hook이 자동 적용됩니다.

### 1.3 인프라 검증

첫 실행 시 자동으로 `setup_init.py`가 인프라 건강을 검증합니다. 수동 검증이 필요하면:

```
/install
```

---

## 2. 설교 워크플로우 시작

### 2.1 시작 방법

```
시작하자
```

또는 직접 커맨드:

```
/sermon-start
```

### 2.2 입력 모드 (3가지)

| Mode | 입력 | 사용 시기 | 예시 |
|------|------|---------|------|
| **Mode A** (기본) | 주제/테마 | 본문이 정해지지 않았을 때 | `고난 중에도 하나님을 신뢰하는 것` |
| **Mode B** | 본문(Pericope) | 본문이 이미 정해졌을 때 | `시편 23:1-6` |
| **Mode C** | 설교시리즈 | 시리즈 설교 중일 때 | `요한복음 강해 시리즈 - 3주차 (요 3:1-21)` |

#### 사용 예시

```
# 주제 기반 (Mode A)
/sermon-start theme 고난 중에도 하나님을 신뢰하는 것

# 본문 직접 입력 (Mode B)
/sermon-start passage 시편 23:1-6

# 설교시리즈 (Mode C)
/sermon-start series 요한복음 강해 시리즈 - 3주차 (요 3:1-21)
```

---

## 3. 워크플로우 단계별 안내

### Phase 0: 초기화

시스템이 자동으로 수행:
- `sermon-output/` 폴더 구조 생성
- `session.json` 초기화 (Context File)
- `todo-checklist.md` 생성 (155단계 체크리스트)
- `state.yaml` 설교 워크플로우 필드 초기화
- `user-resource/` 폴더 확인 (사용자 참고 자료)

#### 사용자 참고 자료 활용

`user-resource/` 폴더에 자료를 넣으면 **최우선 참조**됩니다:

| 우선순위 | 소스 | 설명 |
|---------|------|------|
| 1 (최우선) | `user-resource/` | 사용자 제공 자료 (주석서, 논문 등) |
| 2 | 웹 검색 | 학술 논문, 주석서 |
| 3 | 기본 지식 | AI 내장 지식 |

---

### HITL-1: 본문 선정 (`/sermon-select-passage`)

Mode A일 경우, `@passage-finder`가 주제에 적합한 본문 후보 5-7개를 제시합니다.

**선택 항목:**

```
[본문 선택] 제시된 후보 중 선택 또는 직접 입력

[원문 분석 수준]
 ○ Standard: 단어 연구 + 기본 문법 분석
 ○ Advanced: 구문론 + 담화 분석 포함
 ○ Expert: 본문비평(Textual Criticism) 포함

[연구 범위]
 ☑ 전체 11개 영역 (권장)
 ☐ 선택적 영역만
```

---

### Phase 1: Research (심층 연구)

본문 확정 후, **11개 박사급 전문 에이전트**가 4-Wave로 심층 연구를 수행합니다.

#### Wave 실행 순서

```
Wave 1 (병렬) → Gate 1 → Wave 2 (병렬) → Gate 2 → Wave 3 (병렬) → Gate 3 → Wave 4 → SRCS
```

#### 11개 연구 영역

| # | 에이전트 | 연구 영역 | 출력 파일 |
|---|---------|---------|---------|
| 1 | @original-text-analyst | 히브리어/헬라어 원문 분석 | `01-original-text-analysis.md` |
| 2 | @manuscript-comparator | 번역본/사본 비교 | `02-translation-manuscript-comparison.md` |
| 3 | @structure-analyst | 구조 분석 (교차대구, 포함구조) | `03-structural-analysis.md` |
| 4 | @parallel-passage-analyst | 평행 본문 분석 | `04-parallel-passage-analysis.md` |
| 5 | @theological-analyst | 신학적 분석 | `05-theological-analysis.md` |
| 6 | @literary-analyst | 문학적 분석 (장르, 비유, 상징) | `06-literary-analysis.md` |
| 7 | @rhetorical-analyst | 플롯/수사학적 분석 | `07-rhetorical-analysis.md` |
| 8 | @historical-context-analyst | 역사/문화 맥락 | `08-historical-cultural-context.md` |
| 9 | @keyword-expert | 핵심 단어 심층 연구 | `09-keyword-study.md` |
| 10 | @biblical-geography-expert | 성경지리 연구 | `10-biblical-geography.md` |
| 11 | @historical-cultural-expert | 역사문화적 배경 | `11-historical-cultural-background.md` |

#### GRA 품질 보증

모든 연구 결과는 **GroundedClaim** 형식으로 출력됩니다:
- 각 클레임에 출처(PRIMARY/SECONDARY/TERTIARY)와 신뢰도(0-100) 명시
- Hallucination Firewall로 "모든 학자가 동의" 같은 패턴 차단
- Cross-Validation Gate로 에이전트 간 모순 탐지
- SRCS 4축 평가로 전체 품질 점수 산출

---

### HITL-2: 연구 결과 검토 (`/sermon-review-research`)

11개 연구 결과의 종합 요약과 SRCS 신뢰도 보고서가 표시됩니다.

**선택 항목:**

```
[검토 방식]
 ○ 요약본만 확인 (권장)
 ○ 전체 상세 보고서 확인
 ○ 특정 영역 심층 확인: [영역 선택]

[추가 연구 요청]
 ☐ 특정 영역 보완 연구 요청
 ☐ 추가 참고문헌 조사 요청
 ☐ 낮은 신뢰도 클레임 재검증
```

> **Context Reset Point**: 이 시점 이후 컨텍스트가 리셋되면 `/sermon-resume`으로 자동 복구 가능

---

### HITL-3a: 설교 스타일 선택 (`/sermon-set-style`)

```
[설교 유형]
 ○ 강해설교 (Expository): 본문 순서 따라 해설
 ○ 주제설교 (Topical): 주제 중심 구성
 ○ 내러티브설교 (Narrative): 이야기 형식
 ○ 교리설교 (Doctrinal): 교리 해설 중심
 ○ 전기설교 (Biographical): 인물 중심
 ○ 적용설교 (Applicational): 삶의 적용 중심

[청중 유형]
 ○ 성인 주일예배
 ○ 청년부
 ○ 장년부/시니어
 ○ 새신자/구도자
 ○ 어린이/청소년
 ○ 특별예배 (부활절/성탄절/추수감사절 등)
 ○ 수요예배/새벽기도회
```

---

### HITL-3b: 핵심 메시지 확정 (`/sermon-confirm-message`)

`@message-synthesizer`가 연구 결과를 종합하여 Big Idea, 중심명제, 설교 목적을 도출합니다.

**선택 항목:**

```
[Big Idea 선택]
 ○ 옵션 A: [제안 1]
 ○ 옵션 B: [제안 2]
 ○ 옵션 C: [제안 3]
 ○ 직접 작성

[강조점 조정]
 ☐ 신학적 깊이 강조
 ☐ 실천적 적용 강조
 ☐ 위로와 격려 강조
 ☐ 도전과 결단 강조
```

> **Context Reset Point**

---

### HITL-4: 아웃라인 승인 (`/sermon-approve-outline`)

`@outline-architect`가 확정된 Big Idea 기반으로 설교 구조를 설계합니다.

**선택 항목:**

```
[아웃라인 검토]
 ○ 승인 - 원고 작성 진행
 ○ 수정 요청 - 피드백 제공
 ○ 재구성 요청 - 다른 구조로 재설계

[세부 조정]
 ☐ 포인트 순서 변경
 ☐ 특정 포인트 강화/축소
 ☐ 예시/일러스트레이션 변경 요청
```

---

### Phase 2.5: 스타일 분석 (조건부)

`user-sermon-style-sample/` 폴더에 기존 설교 샘플이 있으면, `@style-analyzer`가 자동으로 문체·어조·구조적 특징을 분석합니다.

**사용법**: 본인의 설교 원고 1-3개를 `user-sermon-style-sample/` 폴더에 넣어두면, 원고 작성 시 해당 스타일이 반영됩니다.

---

### HITL-5a: 원고 포맷 설정 (`/sermon-set-format`)

```
[원고 형식]
 ○ 완전원고형 (Full Manuscript) — 모든 내용을 문장으로
 ○ 반원고형 (Semi-Manuscript) — 핵심 문장 + 상세 노트
 ○ 아웃라인+스크립트 (Outline with Script) — 구조 + 핵심 스크립트

[설교 분량]
 ○ 15분 (약 2,000-2,500자)
 ○ 20분 (약 2,800-3,200자)
 ○ 30분 (약 4,000-4,800자) [기본값]
 ○ 40분 (약 5,500-6,500자)
 ○ 직접 입력: ___분

[문체 선호]
 ○ 격식체 (예배 분위기)
 ○ 대화체 (친근한 분위기)
 ○ 강연체 (강의 분위기)
```

---

### HITL-5b: 최종 검토 (`/sermon-finalize`)

`@sermon-writer`가 원고 초안을 작성하고, `@sermon-reviewer`가 품질 검토 리포트를 생성합니다.

**선택 항목:**

```
[검토 결과]
 ○ 최종 승인 - 완료
 ○ 수정 요청 - 피드백 반영
 ○ 전면 재작성 요청

[수정 요청 유형]
 ☐ 특정 부분 보완 (직접 지정)
 ☐ 예시/일러스트레이션 교체
 ☐ 분량 조정 (늘리기/줄이기)
 ☐ 문체/어조 변경
 ☐ 적용점 강화
```

> **Context Reset Point**

---

## 4. 유틸리티 커맨드

| 커맨드 | 설명 | 사용 시기 |
|--------|------|---------|
| `/sermon-status` | 현재 진행 상태 확인 | 언제든지 |
| `/sermon-resume` | 컨텍스트 리셋 후 자동 재개 | 세션 복구 시 |
| `/sermon-learn-style` | 설교 스타일 수동 분석 | 스타일 분석만 별도로 할 때 |
| `/sermon-evaluate-srcs` | SRCS 평가 수동 실행 | 품질 재평가가 필요할 때 |

---

## 5. 최종 산출물

워크플로우 완료 시 생성되는 파일 구조:

```
sermon-output/[설교제목-YYYY-MM-DD]/
├── session.json                    # 세션 상태
├── todo-checklist.md               # 진행 체크리스트
├── research-package/               # 연구 자료 패키지
│   ├── 01-original-text-analysis.md
│   ├── 02-translation-manuscript-comparison.md
│   ├── 03-structural-analysis.md
│   ├── 04-parallel-passage-analysis.md
│   ├── 05-theological-analysis.md
│   ├── 06-literary-analysis.md
│   ├── 07-rhetorical-analysis.md
│   ├── 08-historical-cultural-context.md
│   ├── 09-keyword-study.md
│   ├── 10-biblical-geography.md
│   └── 11-historical-cultural-background.md
├── research-synthesis.md           # 연구 종합본 (2000-2500자)
├── srcs-summary.json               # SRCS 평가 결과
├── confidence-report.md            # 신뢰도 보고서
├── core-message.md                 # 핵심 메시지 (Big Idea)
├── sermon-outline.md               # 설교 아웃라인
├── style-profile.json              # 스타일 프로파일 (있을 경우)
├── sermon-draft.md                 # 설교 원고 초안
├── review-report.md                # 품질 검토 리포트
└── sermon-final.md                 # 최종 설교 원고
```

---

## 6. 컨텍스트 리셋 복구

### 6.1 자동 복구

컨텍스트 리셋 시, 프레임워크의 `restore_context.py`가 자동으로 세션 포인터를 복원합니다.

### 6.2 수동 복구

```
/sermon-resume
```

이 커맨드는:
1. `session.json`, `todo-checklist.md`, `research-synthesis.md`를 읽음
2. 체크리스트에서 마지막 완료 단계를 파악
3. 다음 단계부터 자동으로 재개

### 6.3 Context Reset Points

| 시점 | 로드할 파일 | 재개 위치 |
|------|-----------|---------|
| HITL-2 이후 | session.json, research-synthesis.md, checklist | Planning Phase |
| HITL-3b 이후 | session.json, outline.md, synthesis, checklist | Implementation Phase |
| HITL-5b 이후 | session.json, sermon-final.md, checklist | 완료 확인 |

---

## 7. 품질 보증 이해하기

### 7.1 SRCS 신뢰도 보고서 읽는 법

HITL-2에서 표시되는 SRCS 보고서의 4축:

| 축 | 의미 | 높은 점수 | 낮은 점수 |
|----|------|---------|---------|
| **CS** (Citation) | 출처 품질 | 권위 있는 출처 다수 인용 | 출처 부족 또는 약한 출처 |
| **GS** (Grounding) | 근거 품질 | 클레임이 출처에 잘 근거함 | 출처와 클레임 간 괴리 |
| **US** (Uncertainty) | 불확실성 표현 | 적절한 불확실성 표현 | 과도한 확신 또는 표현 부재 |
| **VS** (Verifiability) | 검증 가능성 | 독자가 직접 확인 가능 | 확인 불가능한 주장 |

**행동 기준**:
- 70점 이상: 안전하게 사용 가능
- 50-69점: 주의하여 사용, 직접 확인 권장
- 50점 미만: 해당 클레임 사용 자제, 보완 연구 요청

### 7.2 Hallucination Firewall 경고

연구 결과에서 다음 표현이 발견되면 자동 차단 또는 경고됩니다:

| 수준 | 동작 | 예시 패턴 |
|------|------|---------|
| BLOCK | 출력 차단 | "모든 학자가 동의", "100%", "예외 없이" |
| REQUIRE_SOURCE | 출처 없으면 차단 | "정확히 N개", "BC YYYY년" (단독) |
| SOFTEN | 완화 권고 | "확실히", "분명히", "명백히" |
| VERIFY | 검증 태그 | "전통적으로", "OO 박사가 주장" |

---

## 8. 고급 사용법

### 8.1 Autopilot Mode

HITL 체크포인트를 자동 승인하여 무중단 실행:

```
설교 준비해줘 (autopilot) 시편 23편
```

> Autopilot Mode에서도 품질 보증(GRA)은 그대로 동작합니다. HITL 체크포인트만 기본값으로 자동 승인됩니다.

### 8.2 ULW Mode

더 철저한 분석이 필요할 때:

```
설교 준비해줘 ulw 시편 23편
```

ULW 활성화 시:
- 각 에이전트가 최대 3회 재시도 (매번 다른 접근법)
- 모든 작업이 TaskCreate/TaskUpdate로 추적
- 100% 완료 또는 불가 사유 보고

### 8.3 스타일 학습

본인의 설교 스타일을 AI에게 학습시키려면:

1. `user-sermon-style-sample/` 폴더에 기존 설교 원고 1-3개를 넣습니다
2. `/sermon-learn-style` 실행 (또는 워크플로우 중 자동 분석)
3. 생성된 `style-profile.json`이 이후 원고 작성에 반영됩니다

---

## 9. 문제 해결

### 9.1 일반적 문제

| 문제 | 원인 | 해결 |
|------|------|------|
| "PyYAML not found" | Python 패키지 미설치 | `pip install pyyaml` |
| Hook 에러 | 인프라 검증 실패 | `/install` 실행 |
| 연구 결과가 나오지 않음 | 에이전트 실패 | `/sermon-status`로 확인 후 해당 Wave 재실행 |
| 컨텍스트 리셋 | 토큰 한계 초과 | `/sermon-resume`으로 복구 |

### 9.2 SRCS 점수가 낮을 때

1. HITL-2에서 "낮은 신뢰도 클레임 재검증" 선택
2. 해당 영역에 대해 `user-resource/`에 참고 자료 추가
3. 보완 연구 요청

### 9.3 주기적 건강 검진

```
/maintenance
```

시스템 상태 점검: stale archives, knowledge-index 무결성, work_log 크기, doc-code 동기화 검증.
