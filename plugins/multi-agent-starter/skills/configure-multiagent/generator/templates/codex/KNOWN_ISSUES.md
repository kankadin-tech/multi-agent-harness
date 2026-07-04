# 알려진 이슈

해결되지 않은 알려진 결함을 추적한다. 고쳐지면 해당 항목을 닫고(✅) PR 링크를 단다.
시스템이 깨지는 크리티컬은 즉시 수정 대상, 표시·미관 한정은 보류 가능.

출처: multi-agent-starter의 `repo-consistency-audit` (2026-05-19).
상세 근거표(`repo-consistency-audit`)는 공개 배포본에 미포함 — 유지보수자 전용.

---

## KI-1 (audit C3) — 표준 `worker-brief.md`를 쓰면 mat이 워커 목적을 ` ```yaml `로 표시

- **상태**: ✅ 종결 (2026-07-04, 수정안 (a) 적용 — 커밋 `fix(templates): KI-1 종결`)
- **심각도**: 낮음 — 시스템·워커 호출·데이터에 영향 없음. [mat](https://github.com/netwaif/mat) **모니터 화면 표시만** 오염. mat 미사용 시 영향 0.
- **재현**: 항상. `_templates/worker-brief.md` 표준 구조를 그대로 채운 brief를 쓰는 모든 작업.

### 증상

mat의 핵심 화면 요소인 "워커 한 줄 목적"이 실제 Objective가 아니라 문자열 ` ```yaml `로 표시된다.

### 근본 원인

| repo | 파일·라인 | 내용 |
|------|-----------|------|
| starter | `_templates/worker-brief.md` | 1행 `# Brief`(heading), 2–4행 `<!-- -->`(comment), 6행 `## Execution Context`(heading), **8행 ` ```yaml ` fence** |
| mat | `internal/parser/task.go:280` | brief 존재 시 무조건 `w.Purpose = firstMeaningfulLine(brief 내용)` |
| mat | `internal/parser/task.go:499–515` | `firstMeaningfulLine`은 **빈 줄·`#`시작·`<!--`시작만 skip**, 그 다음 줄을 그대로 반환 |
| mat | `internal/parser/task.go:71–76` | `w.Purpose == ""`일 때만 `planned_workers.purpose`로 fallback |

표준 brief에서 heading·comment를 건너뛴 첫 "의미 있는" 줄은 `## Execution Context` 다음의 ` ```yaml ` fence다. 이 값이 비어있지 않으므로 `planned_workers.purpose` fallback도 발동하지 않는다.

### 수정 후보 (택1, 미결정)

- **(a) starter 템플릿** — `_templates/worker-brief.md`를 첫 의미 있는 줄이 실제 한 줄 목적이 되도록 재구성 (예: Execution Context yaml 위에 평문 목적 1줄, 또는 Objective를 평문으로 선두 배치).
  - 장점: starter 단독 수정, mat 재빌드 불필요, 자기완결.
  - 단점: 전 worker 공용 템플릿 변경. 1200자 한도·codex Execution Context yaml 요구와 양립해야.
- **(b) mat 파서** — `firstMeaningfulLine`이 코드펜스(` ``` `/` ```yaml `)도 skip하거나, 명시적 purpose 필드를 우선.
  - 장점: 임의 brief에 견고.
  - 단점: mat 재빌드·재배포 필요(`go build -o mat .` + 재실행). mat은 선택적 외부 도구라 비-mat 환경엔 무의미.


### 종결 기록 (2026-07-04)

- **적용**: 수정안 (a) — `_templates/worker-brief.md` 재구성(root + 번들 3 flavor 동시). 헤딩·주석 직후에 한 줄 목적 평문(placeholder) 배치 → mat `firstMeaningfulLine`이 이 줄을 반환. 2.2.x에서 증상 문자열은 ` ```yaml `이 아니라 "Worker 행동 규약" 첫 불릿으로 바뀌어 있었으나 근본 원인(첫 의미 줄 ≠ 목적)은 동일했음.
- **검증**: mat 파서 규칙(빈 줄·`#`·`<!--` 시작만 skip) 시뮬레이션으로 4개 사본 모두 첫 의미 줄 = 목적 평문 확인. INV1(`tasks-only`)·INV4(`1200자`) 잔존. `init.py` 테스트 설치 + `validate.py` 전체 PASS. codex-critic adversarial 리뷰 반영(2.1.0 기준 검수 후 2.2.2에 이식).
- **잔여 리스크**: (1) 이미 생성된 기존 task의 `workers/*/brief.md`는 자동 갱신 안 됨 — 계속 쓰면 표시 오염 잔존. (2) placeholder 미교체 시 placeholder 문구가 그대로 표시 — 템플릿 주석으로 교체 강제.

---
### 참고

- 공개 흔적: `_shared/learnings.md` [2026-05-19] (곁다리 언급), PR #5 본문.
- 크리티컬 해소 이력: PR #3 (C1 gemini 기본 모델), PR #5 (C2 gemini 단일 브리지).

## KI-4 — `init.py` update 모드가 `_shared/learnings.md` 로컬 누적분을 번들로 덮어씀

- **상태**: 열림 (2026-07-04 발견)
- **심각도**: 중간 — CLAUDE.md Task Lifecycle는 "시스템 일반 교훈 → `_shared/learnings.md`" 적재를 지시하지만, `init.py`의 보존 대상은 `PRESERVE_DIRS = ("tasks", "_local")`뿐이라 update 재실행 시 로컬 append 교훈이 번들본으로 교체·소실된다.
- **재현**: 설치본 `_shared/learnings.md`에 항목 append → `init.py --target <같은 폴더> --yes` (update 모드) → append 항목 소실.
- **완화**: 교훈을 `_local/learnings.md`에 병행 기록, 또는 재설치 전 diff 백업.
- **수정 후보**: `init.py`가 update 모드에서 `learnings.md`를 3-way 병합하거나, 로컬 항목 마커(`<!-- local -->` 이하)를 보존하는 로직 추가.
