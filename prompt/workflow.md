# Sermon Research Workflow v2.0 (설교연구 워크플로우)

설교 본문 선정부터 원고 초안까지, 박사급 전문 분석을 통해 체계적으로 설교를 준비하는 워크플로우.

**GRA(Grounded Research Architecture)** 기반 할루시네이션 방지 및 품질 보증 시스템 적용.

## Overview

- **Input**: 주제/테마(Default) | 본문(Pericope) | 설교시리즈 계획
- **Output**: 설교준비 패키지 + 아웃라인 + 설교 원고 초안
- **Frequency**: On-demand
- **Quality Level**: 박사급 전문가 수준 (토큰 비용 무관, 품질 최우선)
- **Architecture**: GRA (Grounded Research Architecture) + External Memory Strategy

---

## 핵심 아키텍처

### 1. GRA (Grounded Research Architecture)

3계층 품질 보증 시스템으로 할루시네이션을 원천 차단합니다.

```
┌─────────────────────────────────────────────────────────────┐
│                  GRA 3-Layer Architecture                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 1: Agent Self-Verification                            │
│  ├─ GroundedClaim 출력 스키마 준수                          │
│  ├─ Hallucination Firewall 통과                             │
│  └─ Mini-SRCS 자기 평가                                     │
│                                                              │
│  Layer 2: Cross-Validation Gates                             │
│  ├─ Gate 1: Wave 1 → Wave 2 (독립분석 검증)                 │
│  ├─ Gate 2: Wave 2 → Wave 3 (의존분석 검증)                 │
│  └─ Gate 3: Wave 3 → Wave 4 (심층분석 검증)                 │
│                                                              │
│  Layer 3: Unified SRCS Evaluation                            │
│  ├─ 전체 클레임 종합 평가                                   │
│  ├─ 교차 일관성 검사                                        │
│  └─ 최종 품질 인증                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2. External Memory Strategy (3-File Architecture)

컨텍스트 윈도우 한계를 극복하기 위한 외부 메모리 전략입니다.

```
┌─────────────────────────────────────────────────────────────┐
│  External Memory Files (외부 메모리 파일)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1️⃣ Context File (컨텍스트 파일)                            │
│     📄 session.json                                         │
│     - 프로젝트 목표/방향성                                   │
│     - 입력 정보 (본문, 모드)                                 │
│     - 옵션 설정                                              │
│     - context_snapshots (HITL 스냅샷)                        │
│                                                              │
│  2️⃣ Todo File (할 일 파일)                                  │
│     📄 todo-checklist.md                                    │
│     - 155단계 체크리스트                                     │
│     - 완료 표시 [x] / 미완료 [ ]                            │
│     - 마지막 작업 지점 파악용                                │
│                                                              │
│  3️⃣ Insights File (인사이트 파일)                           │
│     📄 research-synthesis.md                                │
│     - 11개 연구 결과 압축본 (2000-2500자)                   │
│     - 핵심 정보만 추출                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3. Context Reset Model

컨텍스트 리셋 시 자동 복구를 위한 체크포인트 시스템입니다.

| 리셋 포인트          | 로드할 파일                                                          | 목적                |
| -------------------- | -------------------------------------------------------------------- | ------------------- |
| **HITL-2 후**  | session.json, research-synthesis.md, research-synthesis.ko.md, checklist | Planning Phase 진입 |
| **HITL-3b 후** | session.json, outline.md, outline.ko.md, synthesis, checklist            | Implementation 진입 |
| **HITL-5b 후** | session.json, sermon-final.md, sermon-final.ko.md, checklist             | 완료 확인           |

---

## Input Mode Selection

워크플로우 시작 시 입력 모드를 확인합니다.

| Mode                       | Input                    | Flow                                                |
| -------------------------- | ------------------------ | --------------------------------------------------- |
| **Mode A** (Default) | 주제/테마                | 주제 분석 → 본문 추천 → 본문 선택                 |
| **Mode B**           | 본문(Pericope) 직접 입력 | 바로 Research 단계 진입                             |
| **Mode C**           | 설교시리즈 계획          | 시리즈 맥락 분석 → 해당 주차 본문 확인 → Research |

---

## Phase 0: Initialization (초기화)

### 0-1. 세션 초기화

- `sermon-output/_temp/` 폴더 생성
- `session.json` 초기화 (Context File)
- `todo-checklist.md` 생성 (Todo File, 155단계)
- `user-resource/` 폴더 확인 (사용자 참고 자료)

### 0-2. 사용자 리소스 관리

`user-resource/` 폴더에 자료를 넣으면 **최우선 참조**됩니다.

| 우선순위   | 소스               | 설명              |
| ---------- | ------------------ | ----------------- |
| 1 (최우선) | `user-resource/` | 사용자 제공 자료  |
| 2          | 웹 검색            | 학술 논문, 주석서 |
| 3          | 기본 지식          | AI 내장 지식      |

---

## Phase 1: Research (연구)

### 1. 본문 선정 프로세스

#### 1-1. [Mode A] 주제 기반 본문 탐색

- **Agent**: `@passage-finder`
- **Task**:
  - 입력된 주제/테마에 적합한 본문 후보 5-7개 도출
  - 각 본문의 적합성 근거 제시
  - 설교 난이도 및 청중 적합성 평가
- **Output**: `passage-candidates.md`
- **Translation**: `@sermon-translator` → `passage-candidates.ko.md` (HITL-1 전 자동 실행)

#### 1-2. [Mode C] 시리즈 맥락 분석

- **Agent**: `@series-analyzer`
- **Task**:
  - 전체 시리즈 흐름에서 해당 주차 위치 파악
  - 이전/이후 설교와의 연결점 분석
  - 시리즈 내 강조점 및 주의사항 도출
- **Output**: `series-context.md`
- **Translation**: `@sermon-translator` → `series-context.ko.md` (HITL-1 전 자동 실행)

### 2. (human) 본문 선정 및 옵션 설정

- **Checkpoint**: `HITL-1`
- **Display**: 본문 후보 목록 + 적합성 분석
- **Options**:
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
- **Command**: `/sermon:select-passage`

---

### 3. 심층 연구 (11개 Sub-agents + GRA)

본문 확정 후, 하이브리드 실행 방식으로 11개 전문 분석 수행.
**모든 에이전트는 GRA 규칙을 준수하여 GroundedClaim 형식으로 출력합니다.**

#### Execution Strategy: Hybrid Parallel-Sequential with Cross-Validation Gates

```
[병렬 실행 - Wave 1: 독립 분석]
┌─ @original-text-analyst (원문 분석)
├─ @manuscript-comparator (번역본/사본 비교)
├─ @biblical-geography-expert (성경지리)
└─ @historical-cultural-expert (역사문화적 배경)
        │
        ▼ [Cross-Validation Gate 1]

[병렬 실행 - Wave 2: 1차 의존 분석]
┌─ @structure-analyst (구조 분석) ← 원문 분석 결과 참조
├─ @parallel-passage-analyst (평행 본문) ← 원문 분석 결과 참조
└─ @keyword-expert (핵심 단어 연구) ← 원문 분석 결과 참조
        │
        ▼ [Cross-Validation Gate 2]

[병렬 실행 - Wave 3: 2차 의존 분석]
┌─ @theological-analyst (신학적 분석) ← 구조 분석 결과 참조
├─ @literary-analyst (문학적 분석) ← 구조 분석 결과 참조
└─ @historical-context-analyst (역사/문화 맥락) ← 배경연구 참조
        │
        ▼ [Cross-Validation Gate 3]

[순차 실행 - Wave 4: 통합 분석]
└─ @rhetorical-analyst (플롯/수사학) ← 문학적 분석 결과 참조
        │
        ▼ [SRCS Full Evaluation]
```

---

#### 3-1. 원문 분석 (Original Text Analysis)

- **Agent**: `@original-text-analyst`
- **Expertise**: 구약 히브리어/신약 헬라어 전문가 (Ph.D. 수준)
- **Task**:
  - 어휘 분석 (Lexical Analysis): 핵심 단어의 의미 범위, 어원
  - 형태론적 분석 (Morphological Analysis): 동사 시제/태/서법, 명사 격/수
  - 구문론적 분석 (Syntactical Analysis): 문장 구조, 절 관계
  - 담화 분석 (Discourse Analysis): 접속사, 담화 표지, 정보 구조
  - [Expert 모드] 본문비평: 주요 사본 이문(異文) 검토
- **GRA Compliance**: GroundedClaim 형식, PRIMARY 출처 필수 (BDB, HALOT, TDOT)
- **Output**: `01-original-text-analysis.md`

#### 3-2. 번역본 및 사본 비교 (Translation & Manuscript Comparison)

- **Agent**: `@manuscript-comparator`
- **Expertise**: 사본학/번역학 전문가
- **Task**:
  - 주요 번역본 비교 (개역개정, 새번역, NIV, ESV, NASB, NRSV 등)
  - 번역 차이가 나는 구절 분석 및 해석적 함의
  - 주요 사본 전통 비교 (NA28, BHS, LXX)
  - 본문비평 장치(Apparatus) 해설
- **GRA Compliance**: GroundedClaim 형식, 사본 출처 명시 필수
- **Output**: `02-translation-manuscript-comparison.md`

#### 3-3. 구조 분석 (Structural Analysis)

- **Agent**: `@structure-analyst`
- **Expertise**: 성경 문학 구조 전문가
- **Task**:
  - 본문의 문학적 단위 구분 (Pericope Delimitation)
  - 대구법, 교차대구(Chiasm), 포함구조(Inclusio) 식별
  - 논증 흐름 또는 서사 흐름 도식화
  - 핵심 구절(Key Verse) 및 정점(Climax) 식별
- **GRA Compliance**: Wave 1 결과와 교차 검증 필수
- **Output**: `03-structural-analysis.md`

#### 3-4. 평행 본문 분석 (Parallel Passage Analysis)

- **Agent**: `@parallel-passage-analyst`
- **Expertise**: 정경 내 상호텍스트성 전문가
- **Task**:
  - 구약 내 평행 본문 (역대기-열왕기, 시편 중복 등)
  - 공관복음 평행 본문 비교
  - 구약 인용/암시 추적 (OT in NT)
  - 신약 내 상호 참조
  - 평행 본문 간 신학적 강조점 차이 분석
- **GRA Compliance**: GroundedClaim 형식, 본문 참조 명시
- **Output**: `04-parallel-passage-analysis.md`

#### 3-5. 신학적 분석 (Theological Analysis)

- **Agent**: `@theological-analyst`
- **Expertise**: 조직신학/성경신학 전문가
- **Task**:
  - 본문의 핵심 신학적 주제 도출
  - 성경신학적 맥락: 구속사적 위치, 언약 신학
  - 주요 신학적 개념 해설 (예: 칭의, 성화, 하나님 나라)
  - 교리적 적용점 및 주의사항
  - 역사적 신학 논쟁 참고 (해당 시)
- **GRA Compliance**: 다양한 신학적 관점 제시 필수, 불확실성 표현 권장
- **Output**: `05-theological-analysis.md`

#### 3-6. 문학적 분석 (Literary Analysis)

- **Agent**: `@literary-analyst`
- **Expertise**: 성경 문학 비평 전문가
- **Task**:
  - 장르 식별 및 장르별 해석 원리 적용
  - 문학적 기법: 비유, 상징, 아이러니, 과장법
  - 서사 기법: 관점, 시간, 인물 묘사
  - 시적 기법: 병행법, 운율, 이미지
  - 저자의 문체적 특징
- **GRA Compliance**: 구조 분석 결과와 교차 검증
- **Output**: `06-literary-analysis.md`

#### 3-7. 플롯 및 수사학적 분석 (Plot & Rhetorical Analysis)

- **Agent**: `@rhetorical-analyst`
- **Expertise**: 고대 수사학 전문가
- **Task**:
  - 서사 플롯 구조: 발단-전개-위기-절정-결말
  - 고대 수사학적 기법 식별 (Greco-Roman Rhetoric)
  - 설득 전략: 에토스, 파토스, 로고스
  - 청중 분석 및 의도된 반응
  - 현대 설교 적용을 위한 수사학적 시사점
- **GRA Compliance**: 문학적 분석 결과 참조, 최종 통합 분석
- **Output**: `07-rhetorical-analysis.md`

#### 3-8. 역사 및 문화 맥락 분석 (Historical-Cultural Context)

- **Agent**: `@historical-context-analyst`
- **Expertise**: 고대 근동/제2성전기 역사 전문가
- **Task**:
  - 저작 연대 및 역사적 상황
  - 저자와 원 청중의 삶의 정황(Sitz im Leben)
  - 관련 고대 근동/헬레니즘 문헌 비교
  - 사회-경제-정치적 배경
  - 종교적 배경 (유대교, 이방 종교)
- **GRA Compliance**: 역사적 연대는 "경", "추정" 등 불확실성 표현 필수
- **Output**: `08-historical-cultural-context.md`

#### 3-9. 설교 핵심 단어 연구 (Key Word Study)

- **Agent**: `@keyword-expert`
- **Expertise**: 성경 어휘론 전문가
- **Task**:
  - 본문 내 설교적으로 중요한 단어 3-5개 선정
  - 각 단어의 심층 연구:
    - 어원 및 의미 발전사
    - 성경 내 용례 분석 (동일 저자, 정경 전체)
    - 동시대 문헌 용례 (LXX, 사해 문서, 헬레니즘 문헌)
    - 신학적 함의
  - 설교 적용을 위한 단어 설명 제안
- **GRA Compliance**: PRIMARY 출처 필수 (Strong's, BDB 등), 용례 수 검증
- **Output**: `09-keyword-study.md`

#### 3-10. 성경지리 연구 (Biblical Geography)

- **Agent**: `@biblical-geography-expert`
- **Expertise**: 성경 고고학/지리학 전문가
- **Task**:
  - 본문 관련 지명 및 지리적 배경
  - 지형, 기후, 거리, 경로 분석
  - 고고학적 발굴 성과 반영
  - 지리가 본문 해석에 미치는 영향
  - 설교 일러스트레이션용 지리 정보
- **GRA Compliance**: 고고학적 출처 명시, 발굴 연대 표시
- **Output**: `10-biblical-geography.md`

#### 3-11. 역사문화적 배경 연구 (Historical-Cultural Background)

- **Agent**: `@historical-cultural-expert`
- **Expertise**: 고대 문화/일상생활 전문가
- **Task**:
  - 관습, 의례, 제도 배경
  - 물질 문화: 의복, 음식, 건축, 도구
  - 사회 구조: 가족, 계층, 직업
  - 일상생활 재구성
  - 현대 청중이 놓치기 쉬운 문화적 뉘앙스
- **GRA Compliance**: SECONDARY 이상 출처 필수
- **Output**: `11-historical-cultural-background.md`

---

### 4. SRCS 평가 (자동)

- **Agent**: `@unified-srcs-evaluator`
- **Task**:
  - 전체 연구 클레임 종합 평가
  - 교차 일관성 검사 (에이전트 간 모순 탐지)
  - 품질 보고서 생성
- **Output**: `srcs-summary.json`, `confidence-report.md`

### 5. 연구 결과 종합

- **Agent**: `@research-synthesizer`
- **Task**:
  - 11개 연구 결과를 2000-2500자로 압축
  - 핵심 인사이트 추출
  - Context Reset 대비 Insights File 생성
- **Output**: `research-synthesis.md`

### 5.5. 연구 결과 한국어 번역 (Translation Layer)

각 Wave의 Gate 통과 후, 해당 Wave의 연구 결과물을 한국어로 번역합니다.
Wave 4 이후에는 `confidence-report.md`와 `research-synthesis.md`도 함께 번역합니다.

- **Agent**: `@sermon-translator` (신학 전문 번역)
- **Execution**: Wave별 병렬 번역 (P1 deterministic routing via `_sermon_lib.get_translation_targets()`)
- **P1 Pipeline**:
  1. `get_translation_targets(phase, output_dir)` → 번역 대상 결정
  2. `build_translation_prompt(source, glossary, output_dir)` → 프롬프트 생성
  3. `@sermon-translator` 실행 (병렬)
  4. `validate_translation_output(source, translation)` → 구조 검증
  5. `extract_translation_pacs(content)` → pACS 점수 추출 (Ft/Ct/Nt/Tt)
  6. `should_retranslate(pacs, retry)` → RED 시 재번역 (최대 2회)
  7. `collect_discovered_terms(files)` → 새 용어 수집
  8. `merge_glossary_terms(glossary, terms)` → 용어 사전 업데이트 (Orchestrator만)
- **Glossary**: `translations/theological-glossary.yaml` (read-only for translators, Orchestrator sole writer)
- **Quality Gate**: Translation pACS = min(Ft, Ct, Nt, Tt) ≥ 70 (GREEN)
- **Output**: 각 `.md` 파일에 대응하는 `.ko.md` 파일 (동일 디렉토리)

```
번역 타이밍:
  Phase 0-A (Mode A) → passage-finder 완료 → 1파일 번역
  Phase 0-C (Mode C) → series-analyzer 완료 → 1파일 번역
  Wave 1 → Gate 1 통과 → 4파일 병렬 번역
  Wave 2 → Gate 2 통과 → 3파일 병렬 번역
  Wave 3 → Gate 3 통과 → 3파일 병렬 번역
  Wave 4 → SRCS 완료 → 3파일 병렬 번역 (rhetorical + confidence + synthesis)
```

### 6. (human) Research 결과 검토

- **Checkpoint**: `HITL-2`
- **Display**:
  - 11개 연구 결과 한국어 번역본 종합 요약
  - SRCS 신뢰도 보고서 (한국어)
  - 검토 필요 클레임 목록
- **Options**:
  ```
  [검토 방식]
  ○ 요약본만 확인 (권장)
  ○ 전체 상세 보고서 확인 (한국어 번역본)
  ○ 특정 영역 심층 확인: [영역 선택]

  [추가 연구 요청]
  ☐ 특정 영역 보완 연구 요청
  ☐ 추가 참고문헌 조사 요청
  ☐ 낮은 신뢰도 클레임 재검증
  ```
- **Command**: `/sermon:review-research`
- **Output**: `research-package.md` (종합본)
- **Context Reset Point**: 이 시점에서 컨텍스트 리셋 가능

---

## Phase 2: Planning (설교 설계)

### 7. 설교 유형 및 청중 설정

#### 7-1. (human) 설교 스타일 선택

- **Checkpoint**: `HITL-3a`
- **Options**:
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
- **Command**: `/sermon:set-style`

### 8. 핵심 메시지 도출

- **Agent**: `@message-synthesizer`
- **Task**:
  - Research 결과 종합하여 Big Idea 도출
  - 중심명제(Central Proposition) 작성
  - 설교 목적(Purpose Statement) 정의
  - 청중 맞춤 적용점 3-5개 도출
- **Output**: `core-message.md`
- **Translation**: `@sermon-translator` → `core-message.ko.md` (HITL-3b 전 자동 실행)

### 9. (human) 핵심 메시지 확정

- **Checkpoint**: `HITL-3b`
- **Display**:
  - Big Idea 제안 (2-3개 옵션, 한국어 — `core-message.ko.md`)
  - 중심명제 제안
  - 설교 목적 제안
- **Options**:
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
- **Command**: `/sermon:confirm-message`
- **Output**: 확정된 Big Idea + 설교 제목
- **Context Reset Point**: 이 시점에서 컨텍스트 리셋 가능

### 10. 설교 아웃라인 작성

- **Agent**: `@outline-architect`
- **Task**:
  - 확정된 Big Idea 기반 설교 구조 설계
  - 설교 유형에 맞는 구성 방식 적용
  - 각 포인트별:
    - 본문 근거
    - 설명 방향
    - 예시/일러스트레이션 제안
    - 적용점
  - 서론/결론 방향 제시
- **Output**: `sermon-outline.md`
- **Translation**: `@sermon-translator` → `sermon-outline.ko.md` (HITL-4 전 자동 실행)

### 11. (human) 아웃라인 승인

- **Checkpoint**: `HITL-4`
- **Display**: 설교 아웃라인 전체 (한국어 — `sermon-outline.ko.md`)
- **Options**:
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
- **Command**: `/sermon:approve-outline`

---

## Phase 2.5: Style Analysis (스타일 분석)

**조건부 실행**: `user-sermon-style-sample/` 폴더에 샘플 존재 시

### 12. 사용자 설교 스타일 분석

- **Agent**: `@style-analyzer`
- **Task**:
  - 사용자 제공 설교 샘플 분석
  - 문체, 어조, 구조적 특징 파악
  - 스타일 프로파일 생성
- **Output**: `style-profile.json`

샘플이 없으면 기본 스타일로 진행합니다.

---

## Phase 3: Implementation (원고 작성)

### 13. 원고 형식 선택

#### 13-1. (human) 원고 포맷 설정

- **Checkpoint**: `HITL-5a`
- **Options**:
  ```
  [원고 형식]
  ○ 완전원고형 (Full Manuscript)
    - 모든 내용을 문장으로 작성
    - 읽기용 완성 원고

  ○ 반원고형 (Semi-Manuscript)
    - 핵심 문장 + 상세 노트
    - 주요 전환부와 결론은 완전 문장

  ○ 아웃라인+스크립트 (Outline with Script)
    - 구조화된 아웃라인
    - 핵심 인용구/전환 문장만 스크립트

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
- **Command**: `/sermon:set-format`

### 14. 설교 원고 초안 작성

- **Agent**: `@sermon-writer`
- **Task**:
  - 승인된 아웃라인 기반 원고 작성
  - **스타일 프로파일 최우선 반영** (있을 경우)
  - 선택된 포맷 및 분량 준수
  - 포함 요소:
    - 서론: 주의 환기, 본문 소개
    - 본론: 포인트별 전개
    - 결론: 요약, 적용, 결단 촉구
    - 예시, 일러스트레이션, 인용
    - 전환 문장
  - 원어 설명 시 청중 수준 고려
- **Output**: `sermon-draft.md`
- **Translation**: `@sermon-translator` → `sermon-draft.ko.md`

### 15. 품질 검토

- **Agent**: `@sermon-reviewer`
- **Task**:
  - 신학적 정확성 검토
  - 본문 충실성 점검
  - 논리 흐름 검토
  - 청중 적합성 평가
  - 시간 배분 적절성 확인
  - 언어/문체 일관성 점검
- **Output**: `review-report.md`
- **Translation**: `@sermon-translator` → `review-report.ko.md` (HITL-5b 전 자동 실행)

### 16. (human) 초안 검토 및 수정 요청

- **Checkpoint**: `HITL-5b`
- **Display**: 설교 원고 초안 + 품질 검토 리포트 (한국어 — `.ko.md` 번역본)
- **Options**:
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
- **Command**: `/sermon:finalize`
- **Context Reset Point**: 이 시점에서 컨텍스트 리셋 가능

### 17. 최종 원고 완성

- **Agent**: `@sermon-writer`
- **Task**: 피드백 반영하여 최종본 완성
- **Output**: `sermon-final.md`
- **Translation**: `@sermon-translator` → `sermon-final.ko.md`

---

## GRA Quality Assurance (품질 보증)

### GroundedClaim Schema

모든 연구 에이전트는 다음 형식으로 클레임을 출력합니다:

```yaml
claims:
  - id: "OTA-001"
    text: "רָעָה (ra'ah)는 '목양하다, 돌보다'를 의미한다"
    claim_type: LINGUISTIC
    sources:
      - type: PRIMARY
        reference: "BDB, p.944-945"
        verified: true
      - type: PRIMARY
        reference: "HALOT, vol.3, p.1258"
        verified: true
    confidence: 98
    uncertainty: null
```

### 클레임 유형 (ClaimType)

| 유형          | 설명                    | 기대 신뢰도 | 필수 출처         |
| ------------- | ----------------------- | ----------- | ----------------- |
| FACTUAL       | 검증 가능한 객관적 사실 | 95+         | PRIMARY/SECONDARY |
| LINGUISTIC    | 원어 분석, 어휘 연구    | 90+         | PRIMARY 필수      |
| HISTORICAL    | 역사적 사건, 연대       | 80+         | SECONDARY 이상    |
| THEOLOGICAL   | 신학적 해석, 교리       | 70+         | SECONDARY 이상    |
| INTERPRETIVE  | 본문 해석, 의미 분석    | 70+         | 제한 없음         |
| APPLICATIONAL | 현대적 적용, 실천 제안  | 60+         | 없음              |

### Hallucination Firewall

생성 시점에서 할루시네이션을 차단하는 규칙:

| 레벨                     | 동작             | 패턴 예시                               |
| ------------------------ | ---------------- | --------------------------------------- |
| **BLOCK**          | 출력 차단        | "모든 학자가 동의", "100%", "예외 없이" |
| **REQUIRE_SOURCE** | 출처 없으면 차단 | "정확히 N개", "BC YYYY년" (단독)        |
| **SOFTEN**         | 경고 + 완화 권고 | "확실히", "분명히", "명백히"            |
| **VERIFY**         | 검증 태그 추가   | "OO 박사가 주장", "전통적으로"          |

### SRCS 4축 평가

| 축                                 | 설명               | 가중치 (FACTUAL 기준) |
| ---------------------------------- | ------------------ | --------------------- |
| **CS** (Citation Score)      | 출처 점수          | 0.3                   |
| **GS** (Grounding Score)     | 근거 품질 점수     | 0.4                   |
| **US** (Uncertainty Score)   | 불확실성 표현 점수 | 0.1                   |
| **VS** (Verifiability Score) | 검증가능성 점수    | 0.2                   |

---

## Agent Thinking Process

### CoT (Chain of Thought)

순차적 추론이 필요한 경우:

```
Step 1: [관찰] → Step 2: [분석] → Step 3: [결론]
```

### ToT (Tree of Thought)

복수 가설 탐색이 필요한 경우:

```
       Root: 문제
      /     |     \
   가설A  가설B  가설C
     |      |      |
   검증    검증   검증
     \      |      /
      최종 결론
```

### Thought Loop (최대 3회)

결론 도달까지 반복 사고:

```
Loop 1: 초기 분석 → 부족
Loop 2: 추가 탐색 → 보완 필요
Loop 3: 최종 분석 → 결론 도출
(3회 초과 시 LOOP_EXHAUSTED 반환)
```

---

## Agent Failure Handling

에이전트 실패 시 처리 방식:

| 실패 유형                 | 설명                   | 처리                       |
| ------------------------- | ---------------------- | -------------------------- |
| `LOOP_EXHAUSTED`        | 3회 사고 후에도 미해결 | 부분 결과 + 실패 지점 명시 |
| `SOURCE_UNAVAILABLE`    | 필수 출처 접근 불가    | 대체 출처 탐색 또는 스킵   |
| `INPUT_INVALID`         | 잘못된 입력            | 재입력 요청                |
| `CONFLICT_UNRESOLVABLE` | 모순 해결 불가         | 양쪽 견해 병기             |
| `OUT_OF_SCOPE`          | 범위 이탈              | 범위 내 결과만 반환        |

---

## Final Outputs (최종 산출물)

```
📁 sermon-output/[설교제목-YYYY-MM-DD]/
├── 📄 session.json                   # 세션 상태 (Context File)
├── 📄 todo-checklist.md              # 진행 체크리스트 (Todo File)
├── 📁 research-package/              # 연구 자료 패키지
│   ├── 01-original-text-analysis.md
│   ├── 01-original-text-analysis.ko.md
│   ├── 02-translation-manuscript-comparison.md
│   ├── 02-translation-manuscript-comparison.ko.md
│   ├── 03-structural-analysis.md
│   ├── 03-structural-analysis.ko.md
│   ├── 04-parallel-passage-analysis.md
│   ├── 04-parallel-passage-analysis.ko.md
│   ├── 05-theological-analysis.md
│   ├── 05-theological-analysis.ko.md
│   ├── 06-literary-analysis.md
│   ├── 06-literary-analysis.ko.md
│   ├── 07-rhetorical-analysis.md
│   ├── 07-rhetorical-analysis.ko.md
│   ├── 08-historical-cultural-context.md
│   ├── 08-historical-cultural-context.ko.md
│   ├── 09-keyword-study.md
│   ├── 09-keyword-study.ko.md
│   ├── 10-biblical-geography.md
│   ├── 10-biblical-geography.ko.md
│   ├── 11-historical-cultural-background.md
│   └── 11-historical-cultural-background.ko.md
├── 📄 research-synthesis.md          # 연구 종합본 (Insights File)
├── 📄 research-synthesis.ko.md       # 연구 종합본 (한국어)
├── 📄 srcs-summary.json              # SRCS 평가 결과
├── 📄 confidence-report.md           # 신뢰도 보고서
├── 📄 confidence-report.ko.md        # 신뢰도 보고서 (한국어)
├── 📄 core-message.md                # 핵심 메시지
├── 📄 core-message.ko.md             # 핵심 메시지 (한국어)
├── 📄 sermon-outline.md              # 설교 아웃라인
├── 📄 sermon-outline.ko.md           # 설교 아웃라인 (한국어)
├── 📄 style-profile.json             # 스타일 프로파일 (선택)
├── 📄 sermon-draft.md                # 설교 원고 초안
├── 📄 sermon-draft.ko.md             # 설교 원고 초안 (한국어)
├── 📄 review-report.md               # 품질 검토 리포트
├── 📄 review-report.ko.md            # 품질 검토 리포트 (한국어)
├── 📄 sermon-final.md                # 최종 설교 원고
└── 📄 sermon-final.ko.md             # 최종 설교 원고 (한국어)
```

---

## Claude Code Configuration

### Sub-agents (26개)

```yaml
agents:
  # Phase 0: Input Processing
  passage-finder:
    description: "주제/테마 기반 적합한 설교 본문 탐색 전문가"
    expertise: "성경신학, 주제별 성경 연구"

  series-analyzer:
    description: "설교 시리즈 맥락 분석 전문가"
    expertise: "설교학, 커리큘럼 설계"

  # Phase 1: Research (11 Doctoral-level Agents)
  original-text-analyst:
    description: "히브리어/헬라어 원문 분석 전문가 (Ph.D.)"
    expertise: "성경 언어학, 본문비평"
    gra_compliance: true
    claim_prefix: "OTA"

  manuscript-comparator:
    description: "번역본 및 사본 비교 분석 전문가"
    expertise: "사본학, 번역학"
    gra_compliance: true
    claim_prefix: "MC"

  structure-analyst:
    description: "성경 본문 구조 분석 전문가"
    expertise: "문학 구조, 담화 분석"
    depends_on: [original-text-analyst]
    gra_compliance: true
    claim_prefix: "SA"

  parallel-passage-analyst:
    description: "평행 본문 분석 전문가"
    expertise: "정경 내 상호텍스트성"
    depends_on: [original-text-analyst]
    gra_compliance: true
    claim_prefix: "PPA"

  theological-analyst:
    description: "신학적 분석 전문가"
    expertise: "조직신학, 성경신학"
    depends_on: [structure-analyst]
    gra_compliance: true
    claim_prefix: "TA"

  literary-analyst:
    description: "문학적 분석 전문가"
    expertise: "성경 문학 비평"
    depends_on: [structure-analyst]
    gra_compliance: true
    claim_prefix: "LA"

  rhetorical-analyst:
    description: "플롯 및 수사학 분석 전문가"
    expertise: "고대 수사학, 서사 비평"
    depends_on: [literary-analyst]
    gra_compliance: true
    claim_prefix: "RA"

  historical-context-analyst:
    description: "역사/문화 맥락 분석 전문가"
    expertise: "고대 근동, 제2성전기 역사"
    depends_on: [historical-cultural-expert]
    gra_compliance: true
    claim_prefix: "HCA"

  keyword-expert:
    description: "설교 핵심 단어 연구 전문가"
    expertise: "성경 어휘론, 의미론"
    depends_on: [original-text-analyst]
    gra_compliance: true
    claim_prefix: "KWE"

  biblical-geography-expert:
    description: "성경지리 연구 전문가"
    expertise: "성경 고고학, 지리학"
    gra_compliance: true
    claim_prefix: "BGE"

  historical-cultural-expert:
    description: "역사문화적 배경 연구 전문가"
    expertise: "고대 문화, 일상생활사"
    gra_compliance: true
    claim_prefix: "HCE"

  # Quality Assurance
  unified-srcs-evaluator:
    description: "통합 SRCS 평가 시스템"
    expertise: "품질 검증, 할루시네이션 탐지"
    replaces: [confidence-evaluator, hallucination-detector, groundedness-verifier]

  research-synthesizer:
    description: "연구 결과 종합 및 압축 전문가"
    expertise: "정보 압축, 핵심 추출"

  # Phase 2: Planning
  message-synthesizer:
    description: "연구 결과 종합 및 핵심 메시지 도출"
    expertise: "설교학, 커뮤니케이션"

  outline-architect:
    description: "설교 아웃라인 설계 전문가"
    expertise: "설교 구성론"

  style-analyzer:
    description: "사용자 설교 스타일 분석 전문가"
    expertise: "문체 분석, 스타일 프로파일링"

  # Translation Layer
  sermon-translator:
    description: "신학 전문 영→한 번역 전문가"
    expertise: "신학 번역, 교회 용어, 원어 음역"

  # Phase 3: Implementation
  sermon-writer:
    description: "설교 원고 작성 전문가"
    expertise: "설교 작성, 수사학"
    uses: [style-profile]

  sermon-reviewer:
    description: "설교 원고 품질 검토 전문가"
    expertise: "설교 비평, 신학적 검토"

  # Orchestrator
  sermon-orchestrator:
    description: "설교연구 워크플로우 총괄 오케스트레이터"
    expertise: "워크플로우 관리, 상태 추적"
    model: opus
```

### Slash Commands (12개)

```yaml
commands:
  /sermon:start:
    description: "설교연구 워크플로우 시작"
    args:
      - name: mode
        type: choice
        options: [theme, passage, series]
        default: theme
      - name: input
        type: string
        required: true
    action: "3-File Architecture 초기화 + 모드별 처리"

  /sermon:select-passage:
    description: "본문 선정 및 연구 옵션 설정"
    checkpoint: HITL-1

  /sermon:review-research:
    description: "11개 연구 결과 + SRCS 보고서 검토"
    checkpoint: HITL-2
    context_reset_point: true

  /sermon:set-style:
    description: "설교 유형 및 청중 설정"
    checkpoint: HITL-3a

  /sermon:confirm-message:
    description: "핵심 메시지(Big Idea) 확정"
    checkpoint: HITL-3b
    context_reset_point: true

  /sermon:approve-outline:
    description: "설교 아웃라인 승인"
    checkpoint: HITL-4

  /sermon:set-format:
    description: "원고 형식 및 분량 설정"
    checkpoint: HITL-5a

  /sermon:finalize:
    description: "최종 원고 검토 및 완료"
    checkpoint: HITL-5b
    context_reset_point: true

  /sermon:status:
    description: "현재 워크플로우 진행 상태 확인"
    reads: [session.json, todo-checklist.md]

  /sermon:resume:
    description: "컨텍스트 리셋 후 자동 재개"
    reads: [session.json, todo-checklist.md, research-synthesis.md]
    action: "마지막 완료 지점부터 자동 재개"

  /sermon:learn-style:
    description: "사용자 설교 스타일 분석 (수동)"
    agent: style-analyzer

  /sermon:evaluate-srcs:
    description: "SRCS 평가 수동 실행"
    agent: unified-srcs-evaluator
```

### Execution Configuration

```yaml
execution:
  mode: hybrid

  waves:
    wave-1:
      mode: parallel
      agents:
        - original-text-analyst
        - manuscript-comparator
        - biblical-geography-expert
        - historical-cultural-expert
      gate: gate-1

    wave-2:
      mode: parallel
      depends_on: wave-1
      agents:
        - structure-analyst
        - parallel-passage-analyst
        - keyword-expert
      gate: gate-2

    wave-3:
      mode: parallel
      depends_on: wave-2
      agents:
        - theological-analyst
        - literary-analyst
        - historical-context-analyst
      gate: gate-3

    wave-4:
      mode: sequential
      depends_on: wave-3
      agents:
        - rhetorical-analyst
      evaluation: full-srcs

  auto_pause_on: human

  quality_settings:
    priority: quality_over_cost
    token_limit: unlimited
    model_preference: claude-opus

  gra_settings:
    hallucination_firewall: enabled
    cross_validation_gates: enabled
    srcs_threshold: 70
    grounding_rate_threshold: 90
```

### External Memory Configuration

```yaml
external_memory:
  strategy: 3-file-architecture

  files:
    context_file: session.json
    todo_file: todo-checklist.md
    insights_file: research-synthesis.md

  checklist:
    total_steps: 155
    manager: scripts/checklist_manager.py

  context_reset_points:
    - checkpoint: HITL-2
      load: [session.json, research-synthesis.md, todo-checklist.md]
    - checkpoint: HITL-3b
      load: [session.json, sermon-outline.md, research-synthesis.md]
    - checkpoint: HITL-5b
      load: [session.json, sermon-final.md]

  resume_command: /sermon:resume
```

### Error Handling

```yaml
error_handling:
  on_agent_failure:
    action: handle_by_type
    types:
      LOOP_EXHAUSTED:
        action: return_partial
        notify: true
      SOURCE_UNAVAILABLE:
        action: seek_alternative
        fallback: skip_with_note
      INPUT_INVALID:
        action: request_retry
      CONFLICT_UNRESOLVABLE:
        action: present_both_views
      OUT_OF_SCOPE:
        action: return_in_scope_only

  on_research_incomplete:
    action: partial_proceed
    notify: true
    message: "[영역명] 분석이 불완전합니다. 계속 진행하시겠습니까?"

  on_validation_failure:
    action: request_human_review

  on_srcs_below_threshold:
    action: flag_for_review
    threshold: 70
```

---

## Usage Examples

### Example 1: 주제 기반 시작 (Default Mode)

```
/sermon:start theme 고난 중에도 하나님을 신뢰하는 것
```

### Example 2: 본문 직접 입력

```
/sermon:start passage 시편 23:1-6
```

### Example 3: 설교 시리즈 연계

```
/sermon:start series 요한복음 강해 시리즈 - 3주차 (요 3:1-21)
```

### Example 4: 컨텍스트 리셋 후 재개

```
/sermon:resume
```

### Example 5: 진행 상태 확인

```
/sermon:status
```

---

## 155-Step Workflow Checklist

전체 워크플로우는 155개 세부 단계로 구성되며, `todo-checklist.md`에서 추적됩니다.

### 단계 구성 요약

| Phase                  | 단계 수 | 설명                    |
| ---------------------- | ------- | ----------------------- |
| Phase 0                | 6       | 세션 초기화             |
| Phase 0-A              | 8       | 본문 탐색 (Mode A) +번역|
| HITL-1                 | 3       | 본문 선정               |
| Wave 1                 | 16      | 독립 분석               |
| Wave 1 Translation     | 4       | Wave 1 번역             |
| Wave 2                 | 12      | 의존 분석               |
| Wave 2 Translation     | 3       | Wave 2 번역             |
| Wave 3                 | 12      | 심층 분석               |
| Wave 3 Translation     | 3       | Wave 3 번역             |
| Wave 4                 | 6       | 통합 분석               |
| Wave 4 Translation     | 3       | Wave 4 번역             |
| HITL-2                 | 8       | 연구 검토               |
| Phase 2 Planning       | 20      | 설교 설계 +번역         |
| HITL-3a/3b             | 10      | 스타일/메시지 확정      |
| Phase 2.5              | 4       | 스타일 분석             |
| HITL-4                 | 3       | 아웃라인 승인           |
| Phase 3 Implementation | 24      | 원고 작성 +번역         |
| HITL-5a/5b             | 10      | 형식 설정/최종 승인     |

---

## Version History

| Version | Date       | Changes                                                                                                                                                                                                              |
| ------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1.0.0   | 2025-01-15 | Initial release                                                                                                                                                                                                      |
| 2.0.0   | 2026-01-18 | GRA Architecture, External Memory Strategy, 120-step checklist, Context Reset Model, Hallucination Firewall, Cross-Validation Gates, SRCS 4-axis evaluation, Style Analysis, /resume command, Unified SRCS Evaluator |
| 2.1.0   | 2026-03-06 | Pervasive Korean Translation Layer — @sermon-translator sub-agent, theological-glossary.yaml, 155-step checklist, wave-boundary batch translation, 4-axis translation pACS (Ft/Ct/Nt/Tt), .ko.md output pairs       |
