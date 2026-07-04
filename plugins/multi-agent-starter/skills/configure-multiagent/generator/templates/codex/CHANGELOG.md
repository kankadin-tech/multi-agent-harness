# Changelog

이 파일은 multi-agent-starter (Codex flavor) orchestration 시스템의 주요 변경을 기록한다.

## [0.3.3] - 2026-07-04

### Fixed
- **KI-1 종결 — worker-brief 템플릿 mat 표시 오염**: 첫 의미 줄이 목적 평문이 아니라서 mat 모니터의 "워커 한 줄 목적"이 오염 표시되던 문제. 헤딩·주석 직후 한 줄 목적 평문(placeholder) 배치로 재구성. 기존 작업의 이미 생성된 brief는 자동 갱신되지 않음.

### Added
- **KI-4 등록(KNOWN_ISSUES)**: `init.py` update 모드가 `_shared/learnings.md` 로컬 누적분을 덮어씀 — `_local/learnings.md` 병행 기록 완화책 문서화.

## [0.3.2] - 2026-07-04

### Fixed
- **gemini 워커 폴백 실패 사유 유실** — 디스패처(`call_worker.sh`)가 api 폴백의 필수 env
  (`GEMINI_API_KEY`) 부재 시 실패 사유 없이 죽던 문제를 에러 envelope 반환으로 수정,
  호출 시작 시 폴백 불가 사전 경고 추가.

### Changed
- routing.md gemini — 소스·다중파일 검토 인라인 필수(agy 헤드리스 300s 타임아웃 실측),
  폴백 조건(`GEMINI_API_KEY`) 명문화, 시간 제한 작업 전 경량 스모크 권장.

## [0.3.1] - 2026-07-03

### Fixed
- **gemini(agy) 워커 프롬프트 미전달 수정** — Antigravity CLI 1.0.16에서 `-p` 단축 플래그가
  제거되어 backends.json의 `args_template: ["-p", …]`가 프롬프트를 조용히 무시(모델 미호출·사용량 0).
  `["--prompt", …]`로 교정. 증상: gemini 워커가 온보딩 인사만 반환.

## [0.3.0] - 2026-06-28

### Added
- **opt-in goal 요금가드 배선(`--with-guard`)** — 설치 시 `--with-guard`를 주면 `_shared/guard/`에
  워처(`codex_goal_watch.mjs`)와 README가 들어온다. `codex remote-control start`로 공유 데몬을 띄우고
  워처를 실행하면, `/goal` 루프가 주간 사용량 한도에 닿을 때 `app-server proxy`로 활성 goal thread를
  `thread/goal/clear`해 정지시킨다(Codex는 Stop훅으로 못 멈춰 외부 워처 필요). 기본 미설치, 런타임
  on/off=`coach guard on/off`. 정책은 `coach`(usage-coach, codexbar 의존)가 갖고 미설치·조회실패는
  fail-open. 상세=`_shared/guard/README.md`.

## [0.2.0] - 2026-06-10

카파시(Karpathy) 4원칙을 층별로 도입. 기존 규칙과 충돌 없음(보강).

### Added
- **AGENTS.md "Operating Principles" 섹션** — 4원칙 verbatim 차용 + 층별 적용 규칙(Orchestrator 전용 풀버전).
- **`_templates/worker-brief.md` "Worker 행동 규약" 고정 블록** — 워커층 번역형: ②③ 그대로, ①은 가정 명시·표면화(워커는 one-shot이라 사용자 질문 채널 없음), ④는 오케스트레이터 전용.
- **`_templates/worker-result.md` 체크리스트 항목** — "가정·불일치가 Issues/Caveats에 표면화됨".
- **design-basis D7 / system-invariants INV11** — 층별 적용 결정 명문화 + 자가점검.
- **`NOTICE`** — 출처·라이선스 표기 (multica-ai/andrej-karpathy-skills, MIT 선언·LICENSE 파일 부재).

## [0.1.0] - 2026-06-01

multi-agent-starter를 기반으로 Codex Orchestrator 버전을 생성했다.

### Added

- `AGENTS.md`: Codex 세션용 운영 규칙 정본.
- `_shared/routing.md`: `codex-main`, `claude-critic`, `gemini` 기준 worker routing.
- `_shared/approval-policy.md`: worker 승인과 외부/유료 모델 승인 게이트.
- `_shared/orchestrator-rules.md`: Codex 세션 환경 점검, 시스템 수정·검증, 작업 재진입 프로토콜.
- `_shared/design-basis.md`: Codex fork의 결정 기록.
- `_shared/system-invariants.md`: Codex 버전 자가 점검 스크립트.
- `_templates/*`: Codex worker pool 기준 task/context/log/brief/result/task-folder 템플릿.

### Changed

- Orchestrator를 Claude Code 세션에서 Codex 세션으로 변경.
- 리뷰 worker를 Codex 자기검수 구조에서 `claude-critic` 독립 검수 구조로 변경.

### Excluded

- 원본 `.claude/agents/`
- 원본 `_local/learnings.md`
- 원본의 기존 작업 이력 산출물
