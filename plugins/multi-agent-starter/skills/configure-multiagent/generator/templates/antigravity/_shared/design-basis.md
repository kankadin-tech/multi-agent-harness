# Design Basis — 왜 이 시스템이 이렇게 생겼나

> **로드 정책**: 이 파일은 평소 작업에서 읽지 않는다. 시스템 파일(`AGENTS.md`, `_shared/*`, `_templates/*`)을 수정·검증할 때만 읽는다.

## 0. 출처

- 원본 starter: multi-agent-starter
- Antigravity flavor: multi-agent-starter의 Antigravity(Gemini) orchestrator 파생본
- 4원칙(Operating Principles) 출처: https://github.com/multica-ai/andrej-karpathy-skills (MIT 선언, LICENSE 파일 부재 — 표기는 `NOTICE` 참조)
- 사용자 결정: Antigravity(agy/IDE, Gemini 3.1 Pro High)가 메인 오케스트레이터가 되며, 산출물 비평은 자기벤더(gemini) 자기검수가 아니라 교차벤더 독립성 있는 `codex-critic`이 맡는다. 메인 코딩은 `claude-main`.

## 1. 핵심 개념 → 시스템 규칙 매핑

| 개념 | 시스템 규칙 | 주의 |
|------|-------------|------|
| 컨텍스트 = 유한 attention budget | context.md <= 1500자, brief <= 1200자 | 한도 변경 시 불변식 갱신 |
| Progressive disclosure | sources/ 경로 참조, brief 최소화 | 긴 자료 inline 금지 |
| Filesystem = memory | task/context/log/brief/result | 런타임 상태에 의존하지 않음 |
| Append-only + provenance | log.md append-only, 태그 6종 | 로그 삭제·수정 금지 |
| Never trust upstream | worker result 검증 후 채택 | 모든 worker 출력 사실검증. 지시-데이터 분리(D8a)와 한 몸 |
| Adversarial review | `codex-critic` | Gemini(오케스트레이터) 자기검수로 대체 금지 |
| 최소 worker set | routing.md decision tree | 모든 worker 기본 호출 금지 |
| Fan-in 충돌 해소 | 출처 병기, 사실검증, `[DECISION]` | 다수결 금지 |

## 2. 권위 우선순위

`AGENTS.md` > `_shared/routing.md`·`approval-policy.md`·`orchestrator-rules.md` > `_templates/*`.

충돌 발견 시 낮은 쪽을 높은 쪽에 맞추고, 작업 중인 task의 `log.md`에 `[DECISION]`으로 남긴다.

## 3. 결정 기록

- **D1 write_scope 값 집합** = `none | tasks-only | "패턴"`. `tasks-only`는 `tasks/<task>/` 내부만 쓰는 기본값이다.
- **D2 critic 역할** = Antigravity 버전에서 산출물 리뷰 worker는 `codex-critic`(교차벤더)다. 오케스트레이터가 Gemini라 gemini 자기검수(gemini-critic)는 독립성이 없어 사용하지 않는다.
- **D3 codex-critic 선행조건** = 리뷰 대상 산출물 경로가 존재해야 한다. 대상은 `claude-main`/`codex-main result.md`, Orchestrator 산출물, 기존 코드·문서·소스도 가능하다.
- **D4 gemini 정책** = gemini는 **워커가 아니라 오케스트레이터**(Antigravity agy/IDE, 전역 모델 `gemini-3.1-pro-high`). 멀티모달·긴 문서는 오케스트레이터가 직접 처리하고 **별도 gemini 워커는 두지 않는다**(같은 벤더라 독립성 이득 없음). agy 모델은 전역·계정단위(`/model`)라 gemini 전용 전역을 pro-high로 운용.
- **D5 Orchestrator** = Antigravity(agy/IDE, Gemini 3.1 Pro High) 현재 세션이 단일 Orchestrator다. 별도 long-lived supervisor worker나 worker 재귀 위임 계층은 쓰지 않는다.
- **D6 모델 식별자 표기** = 워커(claude-main/codex-main/codex-critic)는 환경 설정/별칭을 따르고 repo에 버전 문자열을 핀하지 않는다. 오케스트레이터 Gemini는 agy 전역 모델 = `gemini-3.1-pro-high`(전역·계정단위라 per-call 핀 불가).
- **D7 카파시 4원칙 층별 적용** = 오케스트레이터 지침(AGENTS.md "Operating Principles" 섹션) 풀버전 verbatim 차용 / 워커층 유일 정본은 `_templates/worker-brief.md`의 "Worker 행동 규약" 고정 블록 — ②단순함·③외과수술식 그대로 + ①추측전질문은 번역형(워커는 one-shot/headless라 사용자 질문 채널 없음 → 가정 명시·불확실/불일치를 result.md Issues/Caveats에 표면화) / ④목표기반 loop은 오케스트레이터 전용(Verification Checklist 루프와 결합). 워커 brief에 "사용자에게 질문" 지시 금지. 출처: multica-ai/andrej-karpathy-skills (MIT 선언, LICENSE 파일 부재 — `NOTICE` 정본, 2026-06-10 확인).
- **D8 런타임 안전 룰** = 상류 정본(kankadin-tech/multi-agent-harness)의 런타임 안전 결정을 이 flavor에 반영. (a) 지시-데이터 분리: sources/·result.md 내 지시문 불채택(AGENTS.md Verification — 기존 never-trust-upstream 강화). (b) 결정론적 검증 실행기: `_shared/check-invariants.sh`가 판정 정본, system-invariants.md 표는 스펙. (c) learnings.md 통합 패스: 20KB 초과 시 승격·압축. (d) worker 호출 예산: task.md `max_worker_calls` soft gate(하드 중단 아님, 승인 게이트 보완). 기존 원칙의 동방향 강화 — 새 원칙 아님. 출처: 상류 D11 (gist Karpathy-skills v2 대조). (Rationale update 2026-07-05, 2nd pass: (e) the budget is fixed at batch-approval time from `planned_workers` — reconciles the auto-progress preference with the soft gate. (f) host-native subagents are read-only exploration only without approval — blocks bypassing the worker pool for artifact-producing delegation, preserves file-as-memory and audit trail.)

- **D9 볼트 브리지 편입** = 상류 정본(kankadin-tech/multi-agent-harness)의 볼트 브리지 결정을 이 flavor에 반영. 하네스 task 산출물을 knot 계열 LLM Wiki 볼트 inbox로 **단방향 export**하는 브리지 3개 파일(`_shared/adapters/export_to_vault.sh`·`_shared/vault.config`·`_shared/vault-bridge.md`)을 generator 정식 배포로 편입해 모든 설치에 배포한다. 볼트는 무수정 — 닿는 것은 inbox capture 파일뿐이고 분류/분석/연결은 볼트가 `/inbox`→`/ingest`로 독립 수행(볼트 열기는 이 flavor에서 `cd <vault> && agy`). (a) **`vault.config`는 사용자 설정(볼트 경로·기본 도메인)이라 scaffold-once 보존** — 신규 설치엔 제네릭 스캐폴드를 깔되 이미 있으면 덮어쓰지 않는다(init.py `PRESERVE_IF_EXISTS`, PRESERVE_DIRS와 같은 취지). (b) **개인 기본경로 일반화** — 스크립트 `DEFAULT_VAULT`는 `$HOME/vaults/knot`. 볼트 경로 우선순위 `--vault > $KNOT_VAULT > vault.config(vault=) > $HOME/vaults/knot`, `--domain <d>` 하나로 목적지 폴더·frontmatter를 함께 유도(폴더↔frontmatter 일치). 회귀보호 = validate **C1**에 브리지 3파일 required 추가(설치 후 셋 다 존재). 출처: 상류 D9. (2026-07-05)

## 4. 불변식

구체 항목과 점검 명령은 `_shared/system-invariants.md`에 둔다.
