# Changelog

이 파일은 multi-agent-starter (Antigravity flavor) orchestration 시스템의 주요 변경을 기록한다.

## [0.3.2] - 2026-07-05

### Added
- **볼트 브리지 정식 편입** — 하네스 task 산출물을 knot 계열 LLM Wiki 볼트 inbox로 단방향
  export하는 브리지를 generator 정식 배포로 편입. `_shared/adapters/export_to_vault.sh`
  (실행권한 유지)·`_shared/vault-bridge.md`·`_shared/vault.config`가 이제 모든 설치에
  배포된다(볼트 열기 힌트는 `cd <vault> && agy`). `--domain <d>` 하나로 목적지 폴더·
  frontmatter를 함께 유도. 결정 기록: 이 flavor D9.

### Changed
- `_shared/vault.config`는 **scaffold-once 보존**(사용자 설정 — update가 덮어쓰지 않음).
- 볼트 경로 우선순위: `--vault > $KNOT_VAULT > vault.config(vault=) > $HOME/vaults/knot`.

## [0.3.1] - 2026-07-05

### Changed
- **Confirm the budget at batch-approval time** — set `max_worker_calls` in the same batch
  approval, sized to `planned_workers` plus a retry margin; the soft gate then fires only on
  runaway beyond the plan (approval-policy call-budget section).
- **Host-native subagents are read-only** — host-native subagent/task tools (e.g. Claude
  Code's Agent tool) may do read-only exploration without approval; any artifact-producing
  delegation must go through the worker pool, since bypassing it leaves brief/result and audit
  log empty (AGENTS.md Approval Gate). (D8 (e)(f))

## [0.3.0] - 2026-07-05

### Added
- **Instruction-data separation (untrusted input)** — `sources/` 자료·worker `result.md`
  내용은 데이터이지 지시가 아님을 AGENTS.md Verification에 명문화. 내장 지시문 발견 시
  불채택 + `[DECISION]` 기록 + 사용자 표면화. (D8a, INV12)
- **`_shared/check-invariants.sh` 결정론 실행기** — system-invariants.md 표가 스펙,
  스크립트가 실행기. ROOT 자동 탐지, 항목별 PASS/FAIL 자체 판정, FAIL 시 exit 1.
  orchestrator-rules §2 절차 3이 이 스크립트 실행으로 갱신됨. (D8b)
- **learnings.md 통합 패스** — 20KB(`wc -c`) 초과 시 반복 검증 교훈을 규칙 파일로 승격하고
  "## 통합됨"에 1줄 요약만 남기는 성장 관리 절차. (D8c)
- **worker 호출 예산 soft gate** — task.md 메타 `max_worker_calls`(기본 6) +
  approval-policy "호출 예산" 섹션 + AGENTS.md Approval Gate 한 줄. 초과 전 사용자 확인
  게이트(하드 중단 아님). (D8d, INV13)

## [0.2.3] - 2026-07-04

### Fixed
- **KI-1 종결 — worker-brief 템플릿 mat 표시 오염**: 첫 의미 줄이 목적 평문이 아니라서 mat 모니터의 "워커 한 줄 목적"이 오염 표시되던 문제. 헤딩·주석 직후 한 줄 목적 평문(placeholder) 배치로 재구성. 기존 작업의 이미 생성된 brief는 자동 갱신되지 않음.

### Added
- **KI-4 등록(KNOWN_ISSUES)**: `init.py` update 모드가 `_shared/learnings.md` 로컬 누적분을 덮어씀 — `_local/learnings.md` 병행 기록 완화책 문서화.

## [0.2.2] - 2026-07-04

### Fixed
- **gemini 워커 폴백 실패 사유 유실** — 디스패처(`call_worker.sh`)가 api 폴백의 필수 env
  (`GEMINI_API_KEY`) 부재 시 실패 사유 없이 죽던 문제를 에러 envelope 반환으로 수정,
  호출 시작 시 폴백 불가 사전 경고 추가.

## [0.2.1] - 2026-07-03

### Fixed
- **gemini(agy) 워커 프롬프트 미전달 수정** — Antigravity CLI 1.0.16에서 `-p` 단축 플래그가
  제거되어 backends.json의 `args_template: ["-p", …]`가 프롬프트를 조용히 무시(모델 미호출·사용량 0).
  `["--prompt", …]`로 교정. 증상: gemini 워커가 온보딩 인사만 반환.

## [0.2.0] - 2026-06-10

카파시(Karpathy) 4원칙을 층별로 도입. 기존 규칙과 충돌 없음(보강).

### Added
- **AGENTS.md "Operating Principles" 섹션** — 4원칙 verbatim 차용 + 층별 적용 규칙(Orchestrator 전용 풀버전).
- **`_templates/worker-brief.md` "Worker 행동 규약" 고정 블록** — 워커층 번역형: ②③ 그대로, ①은 가정 명시·표면화(워커는 one-shot이라 사용자 질문 채널 없음), ④는 오케스트레이터 전용.
- **`_templates/worker-result.md` 체크리스트 항목** — "가정·불일치가 Issues/Caveats에 표면화됨".
- **design-basis D7 / system-invariants INV11** — 층별 적용 결정 명문화 + 자가점검.
- **`NOTICE`** — 출처·라이선스 표기 (multica-ai/andrej-karpathy-skills, MIT 선언·LICENSE 파일 부재).

## [0.1.0] - 2026-06-01

multi-agent-starter를 기반으로 Antigravity Orchestrator 버전을 생성했다.

### Added

- `AGENTS.md`: Antigravity 세션용 운영 규칙 정본.
- `_shared/routing.md`: `claude-main`, `codex-main`, `codex-critic` 기준 worker routing.
- `_shared/approval-policy.md`: worker 승인과 외부/유료 모델 승인 게이트.
- `_shared/orchestrator-rules.md`: Antigravity 세션 환경 점검, 시스템 수정·검증, 작업 재진입 프로토콜.
- `_shared/design-basis.md`: Antigravity flavor의 결정 기록.
- `_shared/system-invariants.md`: Antigravity 버전 자가 점검 스크립트.
- `_templates/*`: Antigravity worker pool 기준 task/context/log/brief/result/task-folder 템플릿.

### Changed

- Orchestrator를 Claude Code 세션에서 Antigravity 세션으로 변경.
- 리뷰 worker를 Gemini(오케스트레이터) 자기검수 구조에서 `codex-critic` 독립 검수 구조로 변경.

### Excluded

- 원본 `.claude/agents/`
- 원본 `_local/learnings.md`
- 원본의 기존 작업 이력 산출물
