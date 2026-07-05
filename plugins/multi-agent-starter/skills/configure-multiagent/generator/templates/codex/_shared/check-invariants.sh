#!/usr/bin/env bash
# System invariant checker — 정본 실행기. 스펙은 _shared/system-invariants.md.
# bash 3.2 compatible. deps: grep/sed only.

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

PASS=0
FAIL=0
SKIP=0

pass() { PASS=$((PASS + 1)); echo "PASS $1"; }
fail() { FAIL=$((FAIL + 1)); echo "FAIL $1"; }
skip() { SKIP=$((SKIP + 1)); echo "SKIP $1"; }

# INV1 — write_scope 값 집합(tasks-only)이 4개 파일에 모두 존재
inv1_ok=1
for f in "$ROOT/AGENTS.md" "$ROOT/_shared/routing.md" \
         "$ROOT/_templates/worker-brief.md" "$ROOT/_templates/task-folder.md"; do
  grep -q 'tasks-only' "$f" 2>/dev/null || inv1_ok=0
done
[ "$inv1_ok" = 1 ] && pass "INV1 write_scope tasks-only 4개 파일 존재" \
                    || fail "INV1 write_scope tasks-only 누락"

# INV2 — codex-critic 활성 참조 없어야 PASS (자기검수 금지)
if grep -rn 'codex-critic' "$ROOT/AGENTS.md" "$ROOT/README.md" \
     "$ROOT/_shared/routing.md" "$ROOT/_shared/approval-policy.md" \
     "$ROOT/_shared/orchestrator-rules.md" "$ROOT/_templates" >/dev/null 2>&1; then
  fail "INV2 codex-critic 활성 참조 존재"
else
  pass "INV2 codex-critic 활성 참조 없음"
fi

# INV3 — claude-critic 비평 워커 존재
if grep -rn 'claude-critic' "$ROOT/AGENTS.md" "$ROOT/_shared/routing.md" "$ROOT/_templates" >/dev/null 2>&1; then
  pass "INV3 claude-critic 존재"
else
  fail "INV3 claude-critic 없음"
fi

# INV4 — log 태그 6종
if grep -q 'DECISION | WORKER_CALL | VERIFICATION | ERROR | APPROVAL | COMPLETE' \
     "$ROOT/_templates/log.md" && \
   grep -q 'DECISION | WORKER_CALL | VERIFICATION | ERROR | APPROVAL | COMPLETE' \
     "$ROOT/AGENTS.md"; then
  pass "INV4 log 태그 6종 일치"
else
  fail "INV4 log 태그 6종 불일치"
fi

# INV5 — context/brief 한도 수치
if grep -rq '1500자\|1200자\|1500 chars\|1200 chars' \
     "$ROOT/AGENTS.md" "$ROOT/_templates/context.md" "$ROOT/_templates/worker-brief.md"; then
  pass "INV5 한도 수치 존재"
else
  fail "INV5 한도 수치 누락"
fi

# INV6 — 권위 우선순위 기록
if grep -rq 'AGENTS.md.*routing.md' \
     "$ROOT/_shared/design-basis.md" "$ROOT/_shared/orchestrator-rules.md"; then
  pass "INV6 권위 우선순위 기록"
else
  fail "INV6 권위 우선순위 누락"
fi

# INV7 — 재진입 프로토콜 (orchestrator-rules + AGENTS.md 포인터)
if grep -q '재진입 프로토콜' "$ROOT/_shared/orchestrator-rules.md" && \
   grep -q 're-entry protocol\|재진입 프로토콜' "$ROOT/AGENTS.md"; then
  pass "INV7 재진입 프로토콜 양쪽 존재"
else
  fail "INV7 재진입 프로토콜 누락"
fi

# INV8 — 토폴로지 4패턴
inv8_ok=1
for p in 'Pipeline' 'Fan-out/Fan-in' 'Expert Pool' 'Producer-Reviewer'; do
  grep -q "$p" "$ROOT/_shared/routing.md" 2>/dev/null || inv8_ok=0
done
[ "$inv8_ok" = 1 ] && pass "INV8 토폴로지 4패턴 존재" \
                   || fail "INV8 토폴로지 4패턴 누락"

# INV9 — gemini 백엔드: backends.json agy·pro-high 둘 다 존재
if grep -q '"command": "agy"' "$ROOT/_shared/backends.json" && \
   grep -q 'gemini-3.1-pro-high' "$ROOT/_shared/backends.json"; then
  pass "INV9 gemini 백엔드 agy·pro-high 존재"
else
  fail "INV9 gemini 백엔드 agy·pro-high 누락"
fi

# INV10 — 옛 프록시 활성호출 없어야 PASS (폐기문맥 제외)
if grep -rn 'mcp__gemini-pro__\|mcp__gemini__gemini_' \
     "$ROOT/_shared/routing.md" "$ROOT/_templates/task-folder.md" "$ROOT/AGENTS.md" 2>/dev/null \
     | grep -viE '폐기|deprecat' | grep -q .; then
  fail "INV10 옛 프록시 활성호출 존재"
else
  pass "INV10 옛 프록시 활성호출 없음"
fi

# INV11 — 카파시 4원칙: 세 요소 모두 존재
if grep -q 'Operating Principles' "$ROOT/AGENTS.md" && \
   grep -q 'Worker 행동 규약' "$ROOT/_templates/worker-brief.md" && \
   grep -q '표면화' "$ROOT/_templates/worker-result.md"; then
  pass "INV11 Operating Principles + Worker 행동 규약 + 표면화 존재"
else
  fail "INV11 카파시 4원칙 요소 누락"
fi
# INV11b — Worker 행동 규약 블록 안 사용자질문 표현 없어야 PASS
if sed -n '/^## Worker 행동 규약/,/^## Execution/p' "$ROOT/_templates/worker-brief.md" \
     | grep -inE '질문|ask' | grep -q .; then
  fail "INV11b Worker 행동 규약 블록 내 사용자질문 표현 존재"
else
  pass "INV11b Worker 행동 규약 블록 내 사용자질문 표현 없음"
fi

# INV12 — 지시-데이터 분리 규칙이 AGENTS.md Verification에 존재
if grep -q 'Instruction-data separation' "$ROOT/AGENTS.md"; then
  pass "INV12 지시-데이터 분리 규칙 존재"
else
  fail "INV12 지시-데이터 분리 규칙 누락 (D8a)"
fi

# INV13 — max_worker_calls가 task.md와 approval-policy.md 양쪽에 존재
if grep -q 'max_worker_calls' "$ROOT/_templates/task.md" && \
   grep -q 'max_worker_calls' "$ROOT/_shared/approval-policy.md"; then
  pass "INV13 max_worker_calls 양쪽 존재"
else
  fail "INV13 max_worker_calls 누락 (D8d)"
fi

echo "----"
echo "SUMMARY: PASS=$PASS FAIL=$FAIL SKIP=$SKIP"
if [ "$FAIL" -ge 1 ]; then
  echo "RESULT: FAIL"
  exit 1
fi
echo "RESULT: ALL PASS"
exit 0
