# 요금가드 워처 (Codex flavor)

opt-in goal 요금가드의 **Codex 절반**. `--with-guard`로 설치되면 이 폴더(`_shared/guard/`)에 들어온다.
가드 *정책*은 전부 `coach`(usage-coach)가 단일 정본으로 판정하고, 워처는 그 결정을 *집행*만 한다.

## 왜 워처인가
Claude는 Stop 훅(`continue:false`)으로 `/goal` 루프를 인-훅 정지할 수 있지만, Codex의 `/goal`
런타임은 그걸 무시한다(실측). 네이티브 정지 = app-server JSON-RPC `thread/goal/clear`. 그래서 외부
워처가 폴링하다 한도 초과 시 활성 goal thread를 clear한다.

## 사전 준비
1. **codexbar + coach 설치** (가드 데이터·판정). `coach`가 PATH에 있어야 한다. 없으면 워처는
   fail-open(아무것도 정지시키지 않음)으로 조용히 통과한다.
2. **공유 데몬 가동** — remote control 켠 app-server 데몬:
   ```bash
   codex remote-control start
   ```
   대화형 `/goal` 세션이 이 데몬에 붙어 동작해야 워처가 그 thread를 잡을 수 있다.
3. **가드 켜기** — `coach guard on` (런타임 스위치, 벤더 무관 단일 플래그). 끄기 = `coach guard off`.

## 실행
```bash
node _shared/guard/codex_goal_watch.mjs
```
환경변수(선택):
- `GUARD_INTERVAL` — 폴링 주기(초, 기본 60)
- `GUARD_PROVIDERS` — coach에 넘길 provider(기본 `codex`)
- `GUARD_SOCK` — app-server control socket 경로(생략 시 기본)

## 동작
`GUARD_INTERVAL`초마다 `coach --guard-check`로 판정 → 정지 판정이면 `thread/loaded/list`로 현재
로드된 thread를 열거하고, goal이 있는 thread를 `thread/goal/clear`한다. 판정 통과·coach 부재·조회
실패는 전부 fail-open(정지 안 함).

## 끄기
- 임시: `coach guard off` (워처는 coach 결정을 따르므로 즉시 무력화 — 워처를 죽일 필요 없음).
- 완전: 워처 프로세스 Ctrl-C.
