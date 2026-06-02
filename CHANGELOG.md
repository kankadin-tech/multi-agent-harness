# Changelog

이 파일은 multi-agent-starter **패키지/배포**의 버전 이력이다.
**설치된 시스템의 동작** 변경 이력은 생성된 폴더의 `CHANGELOG.md`
(정본: `generator/templates/{claude,codex}/CHANGELOG.md`)를 참조한다.
형식은 [Keep a Changelog](https://keepachangelog.com/), 버전은 [Semantic Versioning](https://semver.org/lang/ko/)을 따른다.

## [2.0.0] - 미배포 (PR 머지 시 태깅)

**Breaking**: 배포 방식을 "clone → 루트 파일 그대로 사용"에서 **생성기 + 플러그인**으로
전환. 이제 repo는 시스템 그 자체가 아니라 시스템을 만들어 주는 도구다.

### Added
- `generator/init.py` — flavor·대상 지정 결정적 생성기 (tasks/·_local/ 보존, dry-run, `--yes`, guard).
- `generator/validate.py` — flavor별 불변식 자가점검 (claude 8 / codex 9), `init`이 설치 후 자동 호출.
- `generator/build_zip.py` — 플러그인 없이 쓰는 자립형 ZIP(run.command/run.bat + 한글 README), 재현가능 빌드.
- `generator/templates/{claude,codex}/` — 두 flavor 정본 템플릿.
- `generator/sync_claude_template.py` — 루트(Claude 정본)에서 `templates/claude` 재생성 + drift 가드.
- `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json` — Claude Code·Codex 플러그인 매니페스트.
- `skills/configure-multiagent/` — "멀티 에이전트 시스템 구성해줘" front door.
- `LICENSE` — MIT.

### Changed
- 배포: clone → 플러그인(`/plugins` 마켓플레이스) / ZIP fallback.
- 루트 문서(README/CHANGELOG/KNOWN_ISSUES)를 repo front-page·패키지 이력으로 분리. 설치된 타깃용 동명 문서는 `templates/` 에 독립 정본으로 둔다.

### Note
- 설치되는 시스템의 **동작**은 1.0.1 라인을 잇는다 — 이번 변경은 *배포/패키징*이지 시스템 규칙 변경이 아니다.

---

> 아래 1.0.x는 generator 전환 이전, **repo가 곧 시스템**이던 시기의 릴리스 이력이다.
> 설치 시스템 동작 이력은 이후 템플릿 CHANGELOG에서 이어진다.

## [1.0.1] - 2026-06-01

모델·추론 정책 표기 정리(문서 patch). 동작 변경 없음.

### Changed
- **모델 식별자 별칭화** (`_shared/routing.md`): claude-main을 버전 문자열(`claude-opus-4-7` 등) 대신 별칭 `opus`로 표기 — 모델이 올라가도 문서 갱신 불필요. codex 예시 일반화, gemini는 `gemini-3.1-pro-low` 핀 유지 + "프록시 업그레이드 시에만 갱신" 노트.
- **claude-main 추론 강도(effort) 명문화**: `effort` 핀 없음 → 세션 `/effort` 상속(현 기본). 고정하려면 frontmatter `effort:`.

### Added
- **design-basis D7**: 모델 식별자 표기 정책(별칭 원칙 / gemini 핀 예외·세부는 D4 정본 / effort 비대칭 근거).

### Verification
- codex-critic adversarial 검수: 치명 0, 권장 3 반영(잔존 핀 제거 포함). INV9/INV10/INV11 PASS, 회귀 없음.

## [1.0.0] - 2026-06-01

첫 버전 태깅. 기존 실사용 시스템을 1.0.0 기준선으로 고정하고, harness(revfactory) 참고 버전 업그레이드를 함께 반영한다.

### Added
- **작업 재진입 프로토콜** (`_shared/orchestrator-rules.md` §3): 콜드세션이 끝난 작업에 다시 들어갈 때 재정박(re-anchor) → 6분기 판단 → 에러 후 진행. `status↔log 불일치`는 다른 분기보다 먼저 적용하는 정규화 단계로 명시.
- **토폴로지 4패턴표** (`_shared/routing.md`): Pipeline / Fan-out·Fan-in / Expert Pool / Producer-Reviewer + Fan-in 규칙.
- **CLAUDE.md** Task Lifecycle에 재진입 프로토콜 포인터.
- **불변식 INV11** (`_shared/system-invariants.md`): 재진입·토폴로지 규정 자동 자가점검(11a/b/c).
- **design-basis D6**: 4패턴 채택 + Supervisor·Hierarchical Delegation 배제 근거.

### Excluded (설계 결정)
- Supervisor·Hierarchical Delegation 패턴: 단일 orchestrator·worker간 무통신·file-as-memory와 충돌하여 미채택 (근거 D6).

### Baseline (1.0.0 시점 핵심 구조)
- 고정 4-worker pool (claude-main / codex-main / codex-critic / gemini), Claude Code 세션 = orchestrator.
- file-as-memory (런타임 상태 0): task / context / log / brief / result.
- 승인 게이트(`workers_approved`), 외부 쓰기 4조건, progressive disclosure(게이트 로드), 권위 우선순위(CLAUDE.md > routing/approval/orchestrator-rules > 매뉴얼).

### Verification
- 배선(INV11a/b/c) PASS · 회귀 없음, 탁상 분기 커버리지, 실전 콜드세션 3/3 PASS, codex-critic adversarial 리뷰 5 ISSUE 반영.

[2.0.0]: https://github.com/netwaif/multi-agent-starter/releases/tag/v2.0.0
[1.0.1]: https://github.com/netwaif/multi-agent-starter/releases/tag/v1.0.1
[1.0.0]: https://github.com/netwaif/multi-agent-starter/releases/tag/v1.0.0
