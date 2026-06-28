#!/usr/bin/env python3
"""L1/A2: 각 flavor를 임시폴더에 생성 → validate가 전부 PASS인지.

외부 호출 없음, 결정적. validate 체크 *개수*는 하드코딩하지 않는다
(F4 등으로 체크가 늘어도 안 깨지도록 — "전부 PASS"와 exit 0만 단언).
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GEN = REPO / "plugins" / "multi-agent-starter" / "skills" / "configure-multiagent" / "generator"
FLAVORS = sorted(p.name for p in (GEN / "templates").iterdir() if p.is_dir())
INSTRUCTION_FILE = {"claude": "CLAUDE.md", "codex": "AGENTS.md", "antigravity": "AGENTS.md"}
KNOT_START, KNOT_END = "<!-- knot:start -->", "<!-- knot:end -->"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True)


def init(tgt: Path, f: str, *, knot: bool = False, guard: bool = False) -> subprocess.CompletedProcess:
    args = [sys.executable, str(GEN / "init.py"),
            "--flavor", f, "--target", str(tgt), "--yes", "--no-validate"]
    if knot:
        args.append("--with-knot")
    if guard:
        args.append("--with-guard")
    return run(args)


def _guard_artifact(tgt: Path, f: str) -> Path:
    """flavor별 --with-guard 산출물 경로(존재 단언용). antigravity는 산출물 없음(None)."""
    return {"claude": tgt / ".claude" / "settings.json",
            "codex": tgt / "_shared" / "guard" / "codex_goal_watch.mjs"}.get(f)


def validate_all_pass() -> int:
    fails = 0
    for f in FLAVORS:
        with tempfile.TemporaryDirectory() as d:
            tgt = Path(d) / f"sys-{f}"
            if init(tgt, f, knot=False).returncode != 0:
                print(f"  FAIL [{f}] init exit nonzero"); fails += 1; continue
            v = run([sys.executable, str(GEN / "validate.py"),
                     "--flavor", f, "--target", str(tgt)])
            ok = v.returncode == 0 and "전부 PASS" in v.stdout
            print(f"  {'PASS' if ok else 'FAIL'} [{f}] validate exit {v.returncode}")
            if not ok:
                print(v.stdout); fails += 1
    return fails


def knot_checks() -> int:
    """--with-knot → 관리블록(C10) 주입 정확성 + 멱등성 + 기본 부재.
    knot 능동 스킬은 플러그인 최상위 skills/knot/ 로 배포(생성물에 복사 안 함, 호스트 네이티브
    로드) → 워크스페이스 스킬 파일 단언 없음."""
    fails = 0
    for f in FLAVORS:
        instr_name = INSTRUCTION_FILE[f]
        # 1) --with-knot → 관리블록 1개 + validate(C10) PASS
        with tempfile.TemporaryDirectory() as d:
            tgt = Path(d) / f"knot-{f}"
            if init(tgt, f, knot=True).returncode != 0:
                print(f"  FAIL [{f}] init --with-knot exit nonzero"); fails += 1; continue
            txt = (tgt / instr_name).read_text(encoding="utf-8")
            block1 = txt.count(KNOT_START) == 1 and txt.count(KNOT_END) == 1
            v = run([sys.executable, str(GEN / "validate.py"),
                     "--flavor", f, "--target", str(tgt)])
            vp = v.returncode == 0 and "전부 PASS" in v.stdout
            ok = block1 and vp
            print(f"  {'PASS' if ok else 'FAIL'} [{f}] --with-knot 관리블록 1개 + validate PASS")
            fails += not ok
            # 2) 멱등 — 재실행 → 블록 여전히 1개
            init(tgt, f, knot=True)
            txt2 = (tgt / instr_name).read_text(encoding="utf-8")
            idem = txt2.count(KNOT_START) == 1 and txt2.count(KNOT_END) == 1
            print(f"  {'PASS' if idem else 'FAIL'} [{f}] --with-knot 멱등(블록 1개)")
            fails += not idem
        # 3) 기본 init → 관리블록 부재
        with tempfile.TemporaryDirectory() as d:
            tgt = Path(d) / f"plain-{f}"
            init(tgt, f, knot=False)
            txt = (tgt / instr_name).read_text(encoding="utf-8")
            absent = KNOT_START not in txt and KNOT_END not in txt
            print(f"  {'PASS' if absent else 'FAIL'} [{f}] 기본 init 관리블록 부재")
            fails += not absent
    return fails


def guard_checks() -> int:
    """--with-guard → 가드 배선(C12) 주입 정확성 + 멱등성 + 기본 부재.
    claude=.claude/settings.json Stop훅, codex=_shared/guard/ 워처, antigravity=산출물 없음(no-op)."""
    fails = 0
    for f in FLAVORS:
        # 1) --with-guard → 산출물 존재(있는 flavor) + validate(C12) PASS
        with tempfile.TemporaryDirectory() as d:
            tgt = Path(d) / f"guard-{f}"
            if init(tgt, f, guard=True).returncode != 0:
                print(f"  FAIL [{f}] init --with-guard exit nonzero"); fails += 1; continue
            art = _guard_artifact(tgt, f)
            present = art is None or art.is_file()   # antigravity: 산출물 없음이 정상
            v = run([sys.executable, str(GEN / "validate.py"),
                     "--flavor", f, "--target", str(tgt)])
            vp = v.returncode == 0 and "전부 PASS" in v.stdout
            ok = present and vp
            print(f"  {'PASS' if ok else 'FAIL'} [{f}] --with-guard 산출물 + validate PASS")
            if not ok and not vp:
                print(v.stdout)
            fails += not ok
            # 2) 멱등 — 재실행 → 여전히 PASS + (claude) Stop guard 항목 1개
            init(tgt, f, guard=True)
            v2 = run([sys.executable, str(GEN / "validate.py"),
                      "--flavor", f, "--target", str(tgt)])
            idem = v2.returncode == 0 and "전부 PASS" in v2.stdout
            if f == "claude":
                import json as _json
                stop = _json.loads(art.read_text(encoding="utf-8")).get("hooks", {}).get("Stop", [])
                guard_n = sum("coach --hook" in _json.dumps(e) for e in stop)
                idem = idem and guard_n == 1
            print(f"  {'PASS' if idem else 'FAIL'} [{f}] --with-guard 멱등")
            fails += not idem
        # 3) 기본 init → 가드 산출물 부재 + validate PASS
        with tempfile.TemporaryDirectory() as d:
            tgt = Path(d) / f"noguard-{f}"
            init(tgt, f)
            art = _guard_artifact(tgt, f)
            absent = art is None or not art.is_file()
            print(f"  {'PASS' if absent else 'FAIL'} [{f}] 기본 init 가드 산출물 부재")
            fails += not absent
    return fails


def main() -> None:
    fails = validate_all_pass() + knot_checks() + guard_checks()
    print(f"test_generate: {'all pass' if not fails else f'{fails} fail'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
