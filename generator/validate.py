#!/usr/bin/env python3
"""생성된 MultiAgent 시스템 자가점검 — flavor별 불변식 검사.

init.py가 설치 후 호출하거나 단독 실행 가능:
    python3 validate.py --flavor codex --target /path/to/system

각 flavor의 system-invariants.md 의도를 구조 검사로 옮긴 것.
PASS/FAIL을 출력하고, 하나라도 FAIL이면 비정상 종료(exit 1).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# flavor별 차이 = 데이터로. (검사 로직은 공유)
FLAVOR = {
    "claude": {
        "instruction": "CLAUDE.md",
        "main_worker": "claude-main",          # routing에 있어야
        "forbidden_worker": None,
        "extra_files": [".claude/agents/claude-main.md", ".mcp.json"],
    },
    "codex": {
        "instruction": "AGENTS.md",
        "main_worker": "claude-critic",         # 리뷰 워커(독립성)
        "forbidden_worker": "codex-critic",     # 자기검수 구조 = 비활성이어야
        "extra_files": [],
    },
}

TOPOLOGY = ("Pipeline", "Fan-out/Fan-in", "Expert Pool", "Producer-Reviewer")
LOG_TAGS = "DECISION | WORKER_CALL | VERIFICATION | ERROR | APPROVAL | COMPLETE"


def read(target: Path, rel: str) -> str | None:
    p = target / rel
    return p.read_text(encoding="utf-8") if p.is_file() else None


def run_checks(target: Path, flavor: str) -> list[tuple[bool, str]]:
    cfg = FLAVOR[flavor]
    results: list[tuple[bool, str]] = []

    def check(ok: bool, msg: str) -> None:
        results.append((bool(ok), msg))

    instr = cfg["instruction"]

    # C1 필수 파일 존재
    required = [
        instr, ".gitignore", "tasks/.gitkeep",
        "_shared/routing.md", "_shared/orchestrator-rules.md",
        "_shared/design-basis.md", "_shared/system-invariants.md",
        "_templates/log.md", "_templates/context.md", "_templates/worker-brief.md",
    ] + cfg["extra_files"]
    missing = [r for r in required if not (target / r).is_file()]
    check(not missing, f"C1 필수 파일 존재 (없음: {missing or '-'})")

    routing = read(target, "_shared/routing.md") or ""
    orch = read(target, "_shared/orchestrator-rules.md") or ""
    instr_txt = read(target, instr) or ""
    log_tpl = read(target, "_templates/log.md") or ""
    brief_tpl = read(target, "_templates/worker-brief.md") or ""

    # C2 log 태그 6종
    check(LOG_TAGS in log_tpl, "C2 log 태그 6종 (_templates/log.md)")

    # C3 컨텍스트/brief 한도 수치
    ctx = read(target, "_templates/context.md") or ""
    check(("1500" in ctx) and ("1200" in brief_tpl), "C3 한도 수치 1500/1200")

    # C4 재진입 프로토콜 (orchestrator-rules + 지침파일 양쪽)
    reentry = ("재진입 프로토콜" in orch) and (("재진입" in instr_txt) or ("re-entry" in instr_txt.lower()))
    check(reentry, "C4 재진입 프로토콜 (orchestrator-rules + 지침파일)")

    # C5 토폴로지 4패턴
    miss_topo = [t for t in TOPOLOGY if t not in routing]
    check(not miss_topo, f"C5 토폴로지 4패턴 (없음: {miss_topo or '-'})")

    # C6 gemini 기본 pro-low, pro-high 격상 아님
    pro_low = "gemini-3.1-pro-low" in routing
    bad_default = bool(re.search(r"pro-high[^\n]*기본|기본[^\n]*pro-high", routing)) and "제외" not in routing
    check(pro_low and not bad_default, "C6 gemini pro-low 기본 (pro-high 미격상)")

    # C7 write_scope 값 일관 (tasks-only 가 지침/routing/brief에 존재)
    ws = all("tasks-only" in t for t in (instr_txt, routing, brief_tpl))
    check(ws, "C7 write_scope tasks-only 분포 (지침/routing/brief)")

    # C8 flavor 워커풀 일관성
    check(cfg["main_worker"] in routing, f"C8 주 워커 '{cfg['main_worker']}' routing에 존재")
    if cfg["forbidden_worker"]:
        active = (cfg["forbidden_worker"] in routing) or (cfg["forbidden_worker"] in instr_txt)
        check(not active, f"C8b 금지 워커 '{cfg['forbidden_worker']}' 활성 참조 없음")

    return results


def main() -> None:
    ap = argparse.ArgumentParser(description="생성된 MultiAgent 시스템 자가점검")
    ap.add_argument("--flavor", choices=tuple(FLAVOR), required=True)
    ap.add_argument("--target", required=True)
    args = ap.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        sys.exit(f"[error] target 폴더 없음: {target}")

    results = run_checks(target, args.flavor)
    print(f"  validate: flavor={args.flavor} target={target}")
    failed = 0
    for ok, msg in results:
        print(f"   [{'PASS' if ok else 'FAIL'}] {msg}")
        failed += not ok
    if failed:
        print(f"\n  {failed}개 FAIL — 생성 결과가 불완전합니다.")
        sys.exit(1)
    print(f"\n  전부 PASS ({len(results)}개).")


if __name__ == "__main__":
    main()
