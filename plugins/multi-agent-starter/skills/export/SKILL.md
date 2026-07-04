---
name: export
description: 하네스 task 산출물을 LLM Wiki 볼트로 전송하는 확정 트리거 — _shared/adapters/export_to_vault.sh 의 얇은 래퍼. 트리거 예시 "/export", "export해줘", "볼트로 보내줘", "vault로 내보내줘", "task 볼트 전송". 하네스 폴더(_shared/adapters/export_to_vault.sh 존재)에서만 동작 — 아니면 안내만 하고 중단. 인자: task명(생략 시 done task 자동 판별), --all, --dry-run, --media copy, --domain <d>.
---

# export — 하네스 task → 볼트 단방향 전송

`export_to_vault.sh`를 부르는 확정 트리거. **로직은 스크립트에만 있다** — 이 스킬은
스크립트를 찾아 호출하는 얇은 shim이다. 전송 규약(경로·frontmatter·no-clobber)의 정본은
`_shared/vault-bridge.md`. 절차를 여기에 재구현하지 않는다.

## 1. 게이트 (먼저)

하네스 루트를 **`$MULTIAGENT_ROOT` 우선 · cwd 상향 탐색 fallback**으로 해석한다:

```bash
R="${MULTIAGENT_ROOT:-}"
if [ -z "$R" ]; then d="$PWD"; while [ "$d" != "/" ]; do
  [ -f "$d/_shared/adapters/export_to_vault.sh" ] && R="$d" && break; d="$(dirname "$d")"; done; fi
[ -n "$R" ] && echo "OK $R" || echo NO_HARNESS
```

`NO_HARNESS`면 실행하지 말고(no-op) 안내한다: "하네스 폴더가 아닙니다. 하네스 설치 폴더에서
다시 실행하거나, 일반 자료 저장은 knot 스킬('knot에 저장해줘')을 쓰세요." 스크립트를 손으로
재구현하거나 볼트에 직접 쓰지 말 것.

## 2. 대상 task 결정

- 사용자가 task명을 줬으면 그대로 사용 (여러 개 가능)
- `--all`이면 전체 배치
- 지정 없으면: `tasks/*/task.md`의 `status:`를 파싱해 **done인 task 중 최근 갱신 1개**를
  기본 후보로 제안. done이 여럿이고 문맥상 어느 것인지 불명확하면 목록을 보여주고 확인받는다.
- done이 아닌 task는 기본 제외. 사용자가 명시 요청하면 "미완료 task" 경고 후 진행.

## 3. 실행·보고

```bash
bash "$R/_shared/adapters/export_to_vault.sh" <task...> [--dry-run] [--media copy] [--domain <d>]
```

- 스크립트 출력(성공 경로/거부 사유)을 그대로 보고. 실패 시 재구현·우회 금지 — 사유를 표면화.
- 성공 시 해당 task의 `log.md`에 append (append-only 규칙 준수):
  `[YYYY-MM-DD HH:MM] [DECISION] 볼트 export: <볼트 내 노트 경로>`
- 후속 안내 한 줄: 볼트에서 별도 세션으로 `/inbox`(분류) → `/ingest`(wiki화·연결).

## Do NOT

- 볼트 파일을 직접 생성·수정하지 말 것 (스크립트만 경유 — no-clobber·slug 규약이 스크립트에 있음)
- 볼트 경로를 추측하지 말 것 (`--vault` > `KNOT_VAULT` > `_shared/vault.config`가 정본)
- 스크립트 부재 시 "대충 복사"로 대신하지 말 것
