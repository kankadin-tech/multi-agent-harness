#!/usr/bin/env bash
# check-invariants.sh — 시스템 불변식 결정론적 실행기
# 스펙 정본: _shared/system-invariants.md (이 스크립트가 실행기, 그 표가 스펙 — 함께 갱신)
# 자동 ROOT 탐지. 각 항목 PASS/FAIL 자체 판정. FAIL 1개 이상이면 exit 1.
# bash 3.2 호환(macOS 기본), 외부 의존성 없음(grep/sed만).

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

FAILS=0
PASSES=0
SKIPS=0

pass() { echo "PASS $1"; PASSES=$((PASSES+1)); }
fail() { echo "FAIL $1"; FAILS=$((FAILS+1)); }
skip() { echo "SKIP $1"; SKIPS=$((SKIPS+1)); }

# expect_all ID desc pattern file...  — 모든 파일에서 최소 1회 매치해야 PASS
expect_all() {
  id="$1"; desc="$2"; pat="$3"; shift 3
  local ok=1
  for f in "$@"; do
    if ! grep -qE "$pat" "$f" 2>/dev/null; then ok=0; fi
  done
  if [ "$ok" -eq 1 ]; then pass "$id $desc"; else fail "$id $desc"; fi
}

# expect_any ID desc pattern file...  — 파일들 중 하나라도 매치하면 PASS
expect_any() {
  id="$1"; desc="$2"; pat="$3"; shift 3
  if grep -qsE "$pat" "$@" 2>/dev/null; then pass "$id $desc"; else fail "$id $desc"; fi
}

# expect_absent ID desc pattern file...  — 어느 파일에서도 매치가 없어야 PASS
expect_absent() {
  id="$1"; desc="$2"; pat="$3"; shift 3
  if grep -qsE "$pat" "$@" 2>/dev/null; then fail "$id $desc"; else pass "$id $desc"; fi
}

# ─────────────────────────────────────────────
# 핵심 점검 (시스템 파일만; 외부 매뉴얼 불필요)
# ─────────────────────────────────────────────

# INV1: write_scope 값(tasks-only)이 CLAUDE.md·routing.md·worker-brief.md·task-folder.md 전부 존재
expect_all "INV1" "write_scope 값(tasks-only) 4개 파일 공통" "tasks-only" \
  "$ROOT/CLAUDE.md" "$ROOT/_shared/routing.md" \
  "$ROOT/_templates/worker-brief.md" "$ROOT/_templates/task-folder.md"

# INV2: codex-critic 전용 강제 표현 없어야 (일반화 표현이어야)
expect_absent "INV2" "codex-critic 전용 강제 표현 없음" \
  'result\.md.? 존재 필수|claude-main 결과 필요 → 항상 후행' \
  "$ROOT/_shared/routing.md"

# INV3: log 태그 6종 정의 라인
expect_any "INV3" "log 태그 6종 정의 (_templates/log.md)" \
  'DECISION \| WORKER_CALL \| VERIFICATION \| ERROR \| APPROVAL \| COMPLETE' \
  "$ROOT/_templates/log.md"

# INV4: 한도 수치 1500자·1200자 (CLAUDE.md·context.md·worker-brief.md)
expect_all "INV4" "한도 수치 1500자 존재" "1500자" \
  "$ROOT/CLAUDE.md" "$ROOT/_templates/context.md"
expect_all "INV4" "한도 수치 1200자 존재" "1200자" \
  "$ROOT/CLAUDE.md" "$ROOT/_templates/worker-brief.md"

# INV6: workers_approved HH:MM 잔존 없어야 (approval-policy.md)
expect_absent "INV6" "workers_approved HH:MM 잔존 없음" \
  'approved_at: <YYYY-MM-DD HH:MM>' \
  "$ROOT/_shared/approval-policy.md"

# INV7: 권위 우선순위 문구 (design-basis.md)
expect_any "INV7" "권위 우선순위 문구 (design-basis.md)" \
  '권위 우선순위|CLAUDE.md가 가장 높|문서가 충돌' \
  "$ROOT/_shared/design-basis.md"

# INV8: 인터랙티브/worktree 금지 (orchestrator-rules.md)
expect_any "INV8" "worktree/백그라운드 금지 (orchestrator-rules.md)" \
  'worktree|배경|백그라운드|background session' \
  "$ROOT/_shared/orchestrator-rules.md"

# INV9: gemini 백엔드 agy cli + pro-high (backends.json)
expect_any "INV9" "backends.json command agy" '"command": "agy"' "$ROOT/_shared/backends.json"
expect_any "INV9" "backends.json gemini-3.1-pro-high" 'gemini-3.1-pro-high' "$ROOT/_shared/backends.json"

# INV10: 폐기 브리지 호출형 mcp__gemini__gemini_* 활성호출 없어야
expect_absent "INV10" "폐기 브리지 호출형 mcp__gemini__gemini_* 없음" \
  'mcp__gemini__gemini_' \
  "$ROOT/_shared/routing.md" "$ROOT/_templates/task-folder.md" "$ROOT/CLAUDE.md"
# INV10b: mcp__gemini__* / mcp__gemini-pro__ 잔여 언급은 전부 '폐기' 문맥이어야
INV10B_BAD=$(grep -rhnE 'mcp__gemini__|mcp__gemini-pro__' \
  "$ROOT/_shared/routing.md" "$ROOT/_templates/task-folder.md" "$ROOT/CLAUDE.md" 2>/dev/null \
  | grep -v '폐기')
if [ -z "$INV10B_BAD" ]; then pass "INV10b 폐기 브리지 잔여 언급 전부 폐기 문맥"; else fail "INV10b 폐기 브리지 잔여 언급 중 비-폐기 문맥 존재"; fi

# INV11a: 재진입 프로토콜 orchestrator-rules §3 + CLAUDE.md 포인터 둘 다
expect_any "INV11a" "재진입 프로토콜 (orchestrator-rules.md)" '재진입 프로토콜' "$ROOT/_shared/orchestrator-rules.md"
expect_any "INV11a" "재진입 프로토콜 포인터 (CLAUDE.md)" '재진입 프로토콜' "$ROOT/CLAUDE.md"
# INV11b: 토폴로지 4패턴 모두 존재
for p in 'Pipeline' 'Fan-out/Fan-in' 'Expert Pool' 'Producer-Reviewer'; do
  expect_any "INV11b" "토폴로지 패턴 $p" "$p" "$ROOT/_shared/routing.md"
done
# INV11c: Supervisor/Hierarchical 은 '배제' 줄에만
INV11C_BAD=$(grep -nE 'Supervisor|Hierarchical' "$ROOT/_shared/routing.md" 2>/dev/null | grep -v '배제')
if [ -z "$INV11C_BAD" ]; then pass "INV11c Supervisor/Hierarchical 배제 줄에만"; else fail "INV11c Supervisor/Hierarchical 배제 외 등장"; fi

# INV12a: 운영 원칙 섹션 (CLAUDE.md)
expect_any "INV12a" "운영 원칙 섹션 (CLAUDE.md)" '운영 원칙 \(Operating Principles\)' "$ROOT/CLAUDE.md"
# INV12b: Worker 행동 규약 고정 블록 (worker-brief.md)
expect_any "INV12b" "Worker 행동 규약 블록 (worker-brief.md)" 'Worker 행동 규약' "$ROOT/_templates/worker-brief.md"
# INV12c: 블록 내 사용자질문 표현 없어야
INV12C_BLOCK=$(sed -n '/^## Worker 행동 규약/,/^## Execution/p' "$ROOT/_templates/worker-brief.md" 2>/dev/null | grep -inE '질문|ask')
if [ -z "$INV12C_BLOCK" ]; then pass "INV12c Worker 규약 블록 내 사용자질문 표현 없음"; else fail "INV12c Worker 규약 블록 내 사용자질문 표현 존재"; fi
# INV12d: result 체크리스트 표면화 항목
expect_any "INV12d" "result 체크리스트 표면화 항목 (worker-result.md)" '표면화' "$ROOT/_templates/worker-result.md"

# INV13: 지시-데이터 분리 규칙이 CLAUDE.md Verification 섹션에 존재
expect_any "INV13" "지시-데이터 분리 규칙 (CLAUDE.md)" '지시-데이터 분리' "$ROOT/CLAUDE.md"

# INV14: max_worker_calls 가 task.md 와 approval-policy.md 양쪽에 존재
expect_all "INV14" "max_worker_calls 양쪽 존재" "max_worker_calls" \
  "$ROOT/_templates/task.md" "$ROOT/_shared/approval-policy.md"

# ─────────────────────────────────────────────
# 유지보수자 전용 (optional): 3 flavor 교차 점검
# ─────────────────────────────────────────────
TPL="$ROOT/plugins/multi-agent-starter/skills/configure-multiagent/generator/templates"
if [ -d "$TPL" ]; then
  expect_all "INV12e" "Operating Principles — codex/antigravity AGENTS.md" 'Operating Principles' \
    "$TPL/codex/AGENTS.md" "$TPL/antigravity/AGENTS.md"
  expect_all "INV12f" "Worker 행동 규약 — 3 flavor worker-brief" 'Worker 행동 규약' \
    "$TPL/claude/_templates/worker-brief.md" \
    "$TPL/codex/_templates/worker-brief.md" \
    "$TPL/antigravity/_templates/worker-brief.md"
else
  skip "INV12e/f generator templates 없음 (설치본 정상)"
fi

# ─────────────────────────────────────────────
# 유지보수자 전용 (optional): 외부 매뉴얼 일관성
# $MANUAL_DIR 설정 시에만 실행
# ─────────────────────────────────────────────
if [ -n "$MANUAL_DIR" ] && [ -f "$MANUAL_DIR/multi-agent-manual.txt" ]; then
  MANUAL="$MANUAL_DIR/multi-agent-manual.txt"
  expect_any "INV5" "매뉴얼 tasks-only" 'tasks-only' "$MANUAL"
  expect_any "INV5" "매뉴얼 한도 1500자" '1500자' "$MANUAL"
  expect_any "INV5" "매뉴얼 한도 1200자" '1200자' "$MANUAL"
  expect_absent "INV5" "매뉴얼 HH:MM 잔존 없음" 'approved_at: <YYYY-MM-DD HH:MM>' "$MANUAL"
  expect_any "INV5" "매뉴얼 권위 우선순위" '권위 우선순위|CLAUDE.md가 가장 높|문서가 충돌' "$MANUAL"
  expect_any "INV5" "매뉴얼 worktree 금지" 'worktree|배경|백그라운드|background session' "$MANUAL"
else
  skip "INV5 외부 매뉴얼 없음 (\$MANUAL_DIR 미설정 — 설치본 정상)"
fi

# ─────────────────────────────────────────────
echo "────────────────────────────────────────"
echo "요약: PASS=$PASSES  FAIL=$FAILS  SKIP=$SKIPS"
if [ "$FAILS" -gt 0 ]; then
  echo "결과: FAIL ($FAILS)"
  exit 1
fi
echo "결과: ALL PASS"
exit 0
