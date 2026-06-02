# multi-agent-starter

파일 기반 멀티에이전트 오케스트레이션 시스템 **생성기**. Claude Code 또는 Codex를
오케스트레이터로 두는 file-as-memory 멀티에이전트 시스템을 원하는 폴더에 결정적으로 만든다.

> v2부터 "clone 후 그대로 사용"이 아니라 **플러그인/생성기**로 배포한다.
> 설치 후 자연어 한 마디 — "멀티 에이전트 시스템 구성해줘" — 면 끝.

## 무엇을 만들어 주나

선택한 **flavor**에 맞는 시스템 파일 한 세트를 대상 폴더에 생성한다:

| flavor | 오케스트레이터 | 워커 풀 |
|--------|----------------|---------|
| `claude` | Claude Code 세션 | claude-main · codex-main · codex-critic · gemini |
| `codex`  | Codex 세션 | codex-main · claude-critic · gemini |

생성되는 시스템에 포함되는 것:

- **승인 게이트** — 모든 워커(외부 모델) 호출 전 명시 승인
- **작업 재진입 프로토콜** — 콜드세션 복귀 시 재정박 → 분기 판단 → 에러 후 진행
- **토폴로지 4패턴** — Pipeline / Fan-out·Fan-in / Expert Pool / Producer-Reviewer
- **불변식 자가점검** — 생성 직후 `validate.py`가 구조를 검증(PASS/FAIL)
- **file-as-memory** — 런타임 상태 0, 모든 결정·승인·검증이 파일로 남는다

생성은 **결정적**이다 — 번들 템플릿을 그대로 복사하며, 모델이 시스템 파일을 창작하지 않는다.

## 설치 & 사용

Claude Code·Codex 모두 **동일한 플러그인 흐름**이다:

1. 호스트에서 `/plugins` 실행
2. **Add Marketplace** 선택 → 저장소 `netwaif/multi-agent-starter` 입력
3. 목록에서 **multi-agent-starter** 를 Enter로 설치·활성화
4. `멀티 에이전트 시스템 구성해줘` → flavor·대상 폴더를 묻고 생성

### ZIP (플러그인 없이 — 최소 기술)

1. [Releases](https://github.com/netwaif/multi-agent-starter/releases)에서 `multi-agent-starter-<버전>.zip` 받아 압축 해제
2. macOS `run.command` / Windows `run.bat` 더블클릭 (또는 폴더에서 `python3 init.py`)
3. 메뉴에서 flavor·대상 폴더 선택

### 직접(개발자) — 생성기 호출

```bash
python3 generator/init.py --flavor <claude|codex> --target "<대상폴더>" --yes
```

설치가 끝나면 자동으로 `validate.py`가 돌며 PASS/FAIL을 보여준다.

## 설치 후

생성된 폴더로 이동해 해당 도구를 실행하고 자연어로 작업을 요청한다:

```
> 새 작업 만들어줘. 목표는 ○○이고 ○○ worker가 필요할 것 같아.
```

Orchestrator가 작업 폴더를 만들고 → 워커 승인을 요청한 뒤 → 진행한다.
운영 규칙 전문은 생성된 폴더의 `CLAUDE.md`(claude) / `AGENTS.md`(codex) 참조.

## 모니터링 (선택) — mat

작업 진행을 터미널에서 지켜보고 싶다면 **[mat](https://github.com/netwaif/mat)** (MultiAgent Tracker)를 함께 쓴다.
한 작업의 워커 상태(대기·실행 중·완료·에러)·goal·로그를 한 화면에서 본다.
시스템을 **읽기만** 하므로 켜두거나 꺼도 진행에 영향이 없다.

```bash
brew install netwaif/tap/mat
MAT_ROOT=<생성된-폴더> mat
```

설치·키 조작 등 자세한 내용은 [mat 저장소](https://github.com/netwaif/mat) 참고.

## 저장소 구조

```
multi-agent-starter/
├── generator/
│   ├── init.py            # 결정적 생성기 (flavor·대상·tasks 보존·dry-run·guard)
│   ├── validate.py        # flavor별 불변식 자가점검
│   ├── build_zip.py       # 자립형 ZIP 빌더 (재현가능)
│   └── templates/{claude,codex}/   # 두 flavor 정본
├── .claude-plugin/marketplace.json # Claude Code 플러그인
├── .codex-plugin/plugin.json       # Codex 플러그인
└── skills/configure-multiagent/    # "구성해줘" front door
```

## 알려진 이슈

해결·보류 중인 알려진 결함은 [`KNOWN_ISSUES.md`](./KNOWN_ISSUES.md)에 추적한다.

## 라이선스

[MIT](./LICENSE)
