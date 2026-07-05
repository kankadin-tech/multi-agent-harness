# Worker Approval Policy

## 원칙

**모든 worker 호출은 작업별로 명시적 승인 필요** (`claude-main`, `codex-main`, `codex-critic` 전체 pool 적용).
`task.md`의 `workers_approved` 리스트에 없으면 호출 금지.

**예외**: Antigravity Orchestrator의 내부 추론은 worker 호출이 아니므로 승인 불필요. 다만 별도 `claude-main`, `codex-main`, `codex-critic` worker 호출은 승인 대상이다.

외부/유료 모델(`claude`, `gemini`, `openai`, `llm`, MCP/agent bridge 등)은 worker 승인과 별도로, 실제 호출 직전에 도구·모델·비용 가능성을 밝히고 사용자 승인을 받아야 한다.

## 승인 절차

1. Orchestrator가 worker 필요성을 판단한다 (`_shared/routing.md` 참조).
2. 사용자에게 다음 정보를 알려 승인 요청:
   - 어떤 worker를
   - 무슨 목적으로
   - 예상 호출 횟수
   - 외부/유료 모델이면 비용·쿼터 가능성
3. 승인 시 `task.md`의 `workers_approved`에 추가.
4. `log.md`에 `[APPROVAL]` 태그로 승인 기록.
5. 같은 작업에서 같은 승인 범위 안의 재호출은 재승인 불필요.

## 승인 예외

- **Orchestrator 내부 추론**: worker 호출이 아니므로 승인 불필요.
- **동일 작업 재호출**: `workers_approved`에 이미 있고 목적·write_scope가 같으면 재승인 불필요.
- **검증 실패 후 재시도**: 승인된 worker 범위 안에서 1회 자동 허용.
- **외부 쓰기 범위 변경**: `target_repo` 또는 `write_scope`가 바뀌면 기존 승인은 무효.

## 호출 예산 (soft gate)

- `task.md` 메타의 `max_worker_calls`(기본 6)는 이 작업의 worker 호출 총 예산이다.
- 예산 초과가 예상되는 호출 전에 사용자 확인을 받는다. 승인 시 `task.md`의 값을 상향하고 `log.md`에 `[DECISION]`으로 기록한다.
- 자동 재시도(orchestrator-rules §3의 1회 재시도)도 예산에 포함된다. 하드 중단이 아니라 확인 게이트다 — 기존 승인 게이트(HITL)를 대체하지 않는다.
- **Confirm the budget at batch-approval time**: when workers are approved as a batch, set `max_worker_calls` in the same approval, sized to the expected call count for `planned_workers` plus a retry margin. The soft gate then fires only on runaway beyond the plan and does not interrupt the user during normal progress.

## 비용·쿼터 가이드라인

| Worker | 예상 비용 | 쿼터 부담 |
|--------|-----------|-----------|
| codex-main | 중간 | Codex 호출 쿼터 |
| codex-critic | 중간 | Codex 호출 쿼터 |
| claude-main | 중간-높음 | Claude API/구독 쿼터 |

## 승인 기록 형식

```yaml
workers_approved:
  - worker: codex-main
    approved_at: <YYYY-MM-DD>
    purpose: 구현 및 로컬 검증
    approved_by: user
  - worker: codex-critic
    approved_at: <YYYY-MM-DD>
    purpose: Antigravity 산출물 리뷰·비평
    approved_by: user
```

날짜 명령어: `date +%Y-%m-%d`
