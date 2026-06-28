---
name: configure-multiagent
description: Use when the user wants to set up / scaffold / install a file-based multi-agent orchestration system in a folder. Triggers on "멀티 에이전트 시스템 구성해줘", "멀티에이전트 세팅", "멀티 에이전트 시스템 만들어줘", "set up a multi-agent system", "configure multi-agent orchestration here". Scaffolds the system (approval gate, task re-entry protocol, topology patterns, invariant self-check) for Claude Code, Codex, or Antigravity via a deterministic generator.
---

# Configure MultiAgent System

이 스킬은 **file-as-memory 멀티에이전트 오케스트레이션 시스템**을 대상 폴더에 생성한다.
**직접 파일을 손으로 쓰지 말 것** — 반드시 이 스킬 폴더에 함께 들어있는 결정적 생성기 `generator/init.py`를 실행한다 (불변식·일관성 보장).

## 절차

1. **flavor 확인** — 사용자에게 묻는다(또는 현재 호스트로 제안):
   - `claude` — Claude Code 오케스트레이터 (워커: claude-main / codex-main / codex-critic / gemini)
   - `codex` — Codex 오케스트레이터 (워커: codex-main / claude-critic / gemini)
   - `antigravity` — Antigravity 오케스트레이터 (Gemini 3.1 Pro High; 워커: claude-main / codex-main / codex-critic, 멀티모달은 오케스트레이터 직접)
2. **대상 폴더 확인** — 어디에 설치할지 묻는다. (상위 폴더 오인 주의 — 정확한 경로를 확인받는다.)
3. **생성기 위치** — `generator/`는 **이 SKILL.md와 같은 폴더 안**에 있다(스킬 자기완결). 호스트별 분기 불필요 — 이 스킬 폴더 기준 `./generator/init.py`. (Claude는 `$CLAUDE_PLUGIN_ROOT/skills/configure-multiagent/generator/init.py`로 해석됨.)
4. **knot 지식 vault 지원? (선택, 기본 미설치)** — `init.py` 실행 직전 한 번 묻는다:
   > "knot 지식 vault 지원도 같이 설치할까요? (선택 — 기본은 미설치)"

   knot = 벤더중립 평문 마크다운 지식 vault. `knot` 능동 스킬(save/ingest/query/lint)은 플러그인에 포함돼 어느 flavor(claude·codex·antigravity)에서든 이미 가용하고 `$KNOT_VAULT` 게이트로 동작한다. 여기서 **예**를 고르면 컨텍스트 파일에 관리블록(자동층)이 추가돼, 에이전트가 작업 중 관련되면 knot을 **알아서 참고**한다. opt-in이라 확실치 않으면 **아니오**(그래도 "knot에 저장" 같은 명시 요청엔 능동 스킬이 동작).
   - **예** → 다음 실행 명령에 `--with-knot`를 붙인다(관리블록 주입).
   - **아니오** → 플래그 없이 진행(능동 스킬은 그대로 가용, 관리블록만 생략).
4b. **goal 요금가드 지원? (선택, 기본 미설치)** — `init.py` 실행 직전 한 번 묻는다:
   > "goal 요금가드도 같이 설치할까요? (선택 — 기본은 미설치. codexbar+coach 필요)"

   요금가드 = `/goal` 자율 루프가 주간 사용량 한도에 닿으면 자동으로 멈추는 벤더중립 안전장치. **예**를 고르면 flavor에 맞는 *배선*만 주입된다(claude=Stop 훅 → `coach --hook`, codex=`_shared/guard/` 워처, antigravity=미지원·no-op). 판정 *정책*은 전부 `coach`(usage-coach, codexbar 의존)가 단일 정본으로 갖고, 미설치·조회실패는 fail-open(작업 안 죽임). 확실치 않으면 **아니오**(나중에 재실행으로 추가 가능). (받기 — coach: https://github.com/netwaif/usage-coach · codexbar: https://github.com/steipete/CodexBar)
   - **예** → 다음 실행 명령에 `--with-guard`를 붙인다(배선 주입).
   - **아니오** → 플래그 없이 진행(가드 배선 생략).
5. **실행** — 확인 후 (이 스킬 폴더의 generator 경로로):
   ```bash
   python3 "<이 스킬 폴더>/generator/init.py" --flavor <claude|codex|antigravity> --target "<대상폴더>" [--with-knot] [--with-guard] --yes
   ```
   `--with-knot`/`--with-guard`는 각각 4·4b단계에서 "예"일 때만 붙인다(둘 다 미설치가 기본). 대화형으로 진행하려면 인자 없이 실행하면 메뉴가 뜬다.
6. **결과 보고** — `init.py`가 끝에 `validate.py`를 자동 실행한다. 그 **PASS/FAIL을 그대로 사용자에게 보고**한다. FAIL이 하나라도 있으면 "완료"라고 말하지 말 것.
7. **knot 후속 안내 (`--with-knot`로 설치한 경우만)** — 결과 보고 뒤 이어서 알린다:
   - vault 경로를 등록해야 활성화된다(미등록이면 완전 no-op). **포인터 파일 한 줄**을 안내한다: `mkdir -p ~/.config/knot && printf '%s\n' "<vault 경로>" > ~/.config/knot/vault` — rc `export`와 달리 GUI에서 띄운 호스트 앱(Codex·Antigravity)에도 닿고 셸 재로딩이 필요 없다. (power-user는 `export KNOT_VAULT=…`도 가능 — env가 파일보다 우선.)
   - vault가 아직 없으면 두 갈래: **(a)** 빈 vault — `knot` 스킬을 부르면 setup(§0b)이 번들 스캐폴드를 복사하고 `git init` 한다. **(b)** 공개 빈 스캐폴드를 직접 클론: `git clone https://github.com/netwaif/knot "<vault 경로>"`.
7b. **요금가드 후속 안내 (`--with-guard`로 설치한 경우만)** — 결과 보고 뒤 이어서 알린다:
   - 활성화 전제: **codexbar + `coach`(PATH에 있어야)** 설치 + `coach guard on`(런타임 스위치, 벤더 무관 단일 플래그). 끄기 = `coach guard off`, 상태·미리보기 = `coach guard status`. 미설치·플래그 off·조회실패는 모두 fail-open(작업 안 죽임).
   - **claude flavor**는 Stop 훅이라 별도 프로세스 불필요(`settings.json` 한 줄로 끝).
   - **codex flavor**는 셋업이 다르다 — 3단계(상세 = `_shared/guard/README.md`): ① 가드용 loopback ws 서버 `codex app-server --listen ws://127.0.0.1:47931`, ② `/goal` 세션을 `codex --remote ws://127.0.0.1:47931`로 시작(같은 서버에 attach — 안 하면 워처가 thread를 못 봄), ③ 워처 `node _shared/guard/codex_goal_watch.mjs`(포트 셋이 동일해야, 기본 47931·env `GUARD_WS_PORT`). ⚠️ loopback 무인증이라 같은 머신 로컬 프로세스가 그 세션을 제어할 수 있음(신뢰된 단일 사용자 머신 가정).

## 동작 보장

- **결정적**: 번들 템플릿을 그대로 복사. 모델이 시스템 파일을 창작하지 않는다.
- **안전**: 대상에 기존 `tasks/`·`_local/` 사용자 데이터가 있으면 보존(update 모드).
- **쓰기 권한**: 파일 생성이므로 쓰기 권한이 필요하다. Codex에서는 `workspace-write` + 승인이 필요할 수 있다 — 막히면 사용자에게 권한을 안내한다.

## Do NOT

- 시스템 파일(CLAUDE.md/AGENTS.md, `_shared/*`, `_templates/*`)을 직접 작성·수정하지 말 것. 항상 `init.py`로 생성.
- 플러그인 자신의 폴더나 `generator/templates/`(이 스킬 폴더 안) 안에 설치하지 말 것 (init.py가 막지만 시도도 금지).
- validate FAIL을 숨기거나 "대충 됐다"고 보고하지 말 것.
