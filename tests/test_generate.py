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


def init(tgt: Path, f: str, *, knot: bool) -> subprocess.CompletedProcess:
    args = [sys.executable, str(GEN / "init.py"),
            "--flavor", f, "--target", str(tgt), "--yes", "--no-validate"]
    if knot:
        args.append("--with-knot")
    return run(args)


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
    """--with-knot 주입 정확성 + 기본 부재 + 멱등성."""
    fails = 0
    for f in FLAVORS:
        instr_name = INSTRUCTION_FILE[f]
        # 1) --with-knot → 마커 사이 블록 정확히 1개 + validate(C10) PASS
        with tempfile.TemporaryDirectory() as d:
            tgt = Path(d) / f"knot-{f}"
            if init(tgt, f, knot=True).returncode != 0:
                print(f"  FAIL [{f}] init --with-knot exit nonzero"); fails += 1; continue
            txt = (tgt / instr_name).read_text(encoding="utf-8")
            present = txt.count(KNOT_START) == 1 and txt.count(KNOT_END) == 1
            v = run([sys.executable, str(GEN / "validate.py"),
                     "--flavor", f, "--target", str(tgt)])
            vp = v.returncode == 0 and "전부 PASS" in v.stdout
            print(f"  {'PASS' if present and vp else 'FAIL'} [{f}] --with-knot 블록 1개 + validate PASS")
            fails += not (present and vp)
            # 3) 멱등 — 같은 타깃에 --with-knot 재실행 → 여전히 1개
            init(tgt, f, knot=True)
            txt2 = (tgt / instr_name).read_text(encoding="utf-8")
            idem = txt2.count(KNOT_START) == 1 and txt2.count(KNOT_END) == 1
            print(f"  {'PASS' if idem else 'FAIL'} [{f}] --with-knot 멱등(블록 여전히 1개)")
            fails += not idem
        # 2) 기본 init → 블록 부재
        with tempfile.TemporaryDirectory() as d:
            tgt = Path(d) / f"plain-{f}"
            init(tgt, f, knot=False)
            txt = (tgt / instr_name).read_text(encoding="utf-8")
            absent = KNOT_START not in txt and KNOT_END not in txt
            print(f"  {'PASS' if absent else 'FAIL'} [{f}] 기본 init 블록 부재")
            fails += not absent
    return fails


def main() -> None:
    fails = validate_all_pass() + knot_checks()
    print(f"test_generate: {'all pass' if not fails else f'{fails} fail'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
