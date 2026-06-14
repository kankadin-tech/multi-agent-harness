---
name: knot
description: $KNOT_VAULT 지식 vault를 직접 다루는 능동 스킬 — verb 4개. save(자료를 inbox에 저장), ingest(prompts/ingest.md 규약으로 컴파일), query(prompts/query.md로 근거기반 질의), lint(scripts/lint.py + prompts/lint.md 건강검진). 트리거 예시 "knot에 저장해줘", "이거 vault에 넣어줘", "knot ingest", "지식그물 컴파일해줘", "knot에 물어봐", "vault에서 찾아줘", "knot lint", "vault 건강검진", "/knot". $KNOT_VAULT 미설정이면 안내만 하고 중단.
---

# knot — 지식 vault 능동 스킬

knot vault를 직접 부르는 4개 동작(save / ingest / query / lint).
**로직은 vault에만 있다** — 이 스킬은 vault 정본(`$KNOT_VAULT/prompts/`·`scripts/`)을
가리키는 얇은 shim이다. 절차 본문을 여기에 옮겨적지 않는다(정본 단일화 — 절차를 고치면
vault 한 곳만 고친다).

## 0. 게이트 (모든 verb 공통 — 먼저)

`$KNOT_VAULT`가 설정돼 있고 실재 디렉토리인지 확인한다:

```bash
[ -n "$KNOT_VAULT" ] && [ -d "$KNOT_VAULT" ] && echo OK || echo NO_VAULT
```

`OK`면 해당 verb로 진행한다. `NO_VAULT`면 verb를 실행하지 말고(no-op) **아래 setup을 제안**한다 —
경로를 추측하거나 임의 폴더에 저장하지 말 것.

## 0b. setup (게이트가 NO_VAULT일 때만)

vault가 아직 없으므로 두 갈래를 제시하고 사용자가 고르게 한다:

- **(a) 기존 vault 경로 사용** — 사용자가 이미 knot vault를 가지고 있으면 그 절대경로를 받는다.
  존재하는 디렉토리인지 확인만 하고, 내용은 건드리지 않는다.
- **(b) 빈 vault 새로 만들기** — 설치할 절대경로를 받아 **번들 스캐폴드를 그대로 복사**한다.
  스캐폴드 정본 = 이 플러그인의 `…/configure-multiagent/generator/knot-vault/`
  (schema·prompts·scripts·미러 3·빈 inbox/raw/wiki). 복사 후 그 경로에서 `git init`:

  ```bash
  cp -R "<플러그인>/skills/configure-multiagent/generator/knot-vault/." "<대상경로>/"
  cd "<대상경로>" && git init
  ```

  스캐폴드 본문을 손으로 재작성하지 말 것 — 번들을 그대로 복사한다(단일 정본).

두 갈래 모두 끝에 `$KNOT_VAULT`를 가리켜야 한다. **rc 파일을 자동 편집하지 말고**, 추가할 줄을
보여주고 사용자가 직접 적용·재로딩하게 한다(비파괴):

```bash
echo 'export KNOT_VAULT="<선택한 경로>"' >> ~/.zshrc   # 사용자가 직접 실행, 셸에 맞게(.bashrc 등)
```

적용 뒤 새 셸에서 게이트를 다시 확인하고 원래 요청한 verb로 진행한다.

## 0c. 무인 drain 등록 (선택 — vault가 준비된 뒤, 사용자가 원할 때만)

inbox를 주기적으로 자동 ingest하려면 OS 스케줄러에 `$KNOT_VAULT/scripts/drain.sh`를 건다.
**drain 로직은 그 스크립트가 정본** — 여기엔 옮겨적지 않는다. 스킬은 스케줄러 항목만 등록한다.
기본은 OFF다. 사용자가 명시적으로 원할 때만 아래를 진행하고, 먼저 묻는다:

```
무인 drain을 등록할까요? (y/N)
 └ y → · 러너? (기본 agy, 또는 claude/codex/gemini)
        · 주기? (예: 매시=3600초 / 매일=86400초)
        · 알림? 데스크톱(기본, 설정 0) / 외부 채널(선택, 아래 ③)
```

**비파괴**: 기존 항목(`com.knot.drain` / 크론 라인)이 이미 있으면 덮어쓰기 전에 사용자에게 확인한다.
**주기·경로·러너는 등록 시 주입**한다 — 번들 템플릿엔 placeholder만 있다(사용자값 하드코딩 금지).

- **mac (launchd)**: 번들 `scripts/launchd.plist.template`의 placeholder 3종
  (`__KNOT_VAULT__`·`__RUNNER__`·`__INTERVAL_SEC__`)을 치환해
  `~/Library/LaunchAgents/com.knot.drain.plist`로 쓰고 로드한다.

  ```bash
  sed -e "s#__KNOT_VAULT__#$KNOT_VAULT#g" -e "s#__RUNNER__#<러너>#g" -e "s#__INTERVAL_SEC__#<초>#g" \
    "$KNOT_VAULT/scripts/launchd.plist.template" > ~/Library/LaunchAgents/com.knot.drain.plist
  launchctl unload ~/Library/LaunchAgents/com.knot.drain.plist 2>/dev/null   # 기존 있으면(확인 후)
  launchctl load ~/Library/LaunchAgents/com.knot.drain.plist
  ```

- **linux (cron)**: drain.sh를 가리키는 한 줄만 crontab에 추가한다(기존 라인 있으면 확인 후 교체).

  ```bash
  # 예: 매시 정각. 주기는 사용자가 고른 cron 식으로.
  ( crontab -l 2>/dev/null | grep -v 'knot/scripts/drain.sh'; \
    echo "0 * * * * KNOT_VAULT=$KNOT_VAULT $KNOT_VAULT/scripts/drain.sh --runner <러너>" ) | crontab -
  ```

**③ 외부 알림 (선택, 비밀값 = vault 밖에만)**: knot vault는 공개될 수 있으므로 웹훅·토큰을 vault 안에
**절대 쓰지 않는다**. 사용자가 외부 채널을 원하면 명령/웹훅을 vault 밖에 둔다 — drain.sh는 참조만 한다:

```bash
mkdir -p ~/.config/knot && chmod 700 ~/.config/knot
# 요약이 인자 $1로 전달된다. 예: Discord 웹훅으로 보내기 — URL은 사용자가 채운다.
cat > ~/.config/knot/notify.sh <<'EOF'
#!/bin/bash
curl -fsS -X POST -H 'Content-Type: application/json' -d "{\"content\": \"$1\"}" "$DISCORD_WEBHOOK_URL"
EOF
chmod +x ~/.config/knot/notify.sh
```

또는 셸 rc에 `export KNOT_NOTIFY_CMD='<요약을 stdin으로 받는 명령>'`. 비우면 데스크톱 알림(②)만 쓴다.
**제거**: `launchctl unload` 후 plist 삭제(mac) / 크론 라인 삭제(linux) + `~/.config/knot/` 정리.

## 1. verb 분기 (사용자 요청으로 판단)

각 verb는 vault 정본을 **읽고 그대로 따른다**. 벤더(Claude / Codex / agy) 무관 — 동일 vault
prompts를 호출한다(벤더 분기 없음).

- **save** — 사용자가 준 자료(텍스트·파일·URL 메모)를 `$KNOT_VAULT/inbox/`에 새 파일로 저장한 뒤
  **그 파일만 커밋**한다. 파일명은 짧은 슬러그. 저장 후
  `git add <그 파일> && git commit -m "save: <슬러그>"` (트레일러에 실행한 실제 모델명,
  예: `Co-Authored-By: <실제 모델명>`). 커밋까지가 save — 그래야 트리가 깨끗해져 다음 ingest의
  클린트리 가드에 막히지 않고, drain 실패복구의 reset도 미커밋 inbox를 지우지 않는다.
  컴파일은 ingest가 한다.
- **ingest** (compile) — `$KNOT_VAULT/prompts/ingest.md`를 정독하고 그 규약을 **그대로 실행**한다
  (inbox/지정 소스 → wiki 컴파일). 절차·단계는 그 파일에 있다.
- **query** (read) — `$KNOT_VAULT/prompts/query.md`를 정독하고 그 규약으로 근거기반 질의응답.
  vault에 근거가 없으면 **지어내지 않고** "근거 없음"이라고 답한다.
- **lint** — `$KNOT_VAULT/scripts/lint.py`를 실행(기계 검사)한 뒤 `$KNOT_VAULT/prompts/lint.md`를
  정독해 의미 진찰(모순·stale·고아·정합)을 수행한다.

## 2. 크로스도구 (벤더중립)

설계상 Claude Code / Codex / agy(Antigravity) 셋 다 같은 vault prompts를 호출한다. 호스트가
스킬을 자동 로드하지 않으면(예: agy의 `activate_skill` 동작이 다를 수 있음) 사용자가
"`$KNOT_VAULT/prompts/<verb>.md`를 정독하고 실행하라"고 직접 지시해도 동일 결과다 — vault 정본이
유일 진실원이기 때문. (agy/Gemini 스킬 활성 경로는 배포 검증에서 확정.)

## Do NOT

- vault 절차 본문을 이 스킬에 복붙하지 말 것 — 항상 `$KNOT_VAULT/prompts/`·`scripts/`를 가리킨다.
- `$KNOT_VAULT` 미설정 시 경로를 추측하거나 임의 폴더에 저장하지 말 것 — 중단·안내.
- query에서 vault에 없는 내용을 지어내지 말 것.
