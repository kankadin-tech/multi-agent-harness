#!/usr/bin/env python3
"""MultiAgent 시스템 생성기 — 결정적(deterministic) 스캐폴더.

flavor 템플릿(claude | codex | antigravity)을 대상 폴더에 복사한다.
- 결정적: 번들된 템플릿 파일을 그대로 복사. LLM 자유작문 없음 → 불변식 보장.
- 안전: 기존 tasks/·_local/ 사용자 데이터를 절대 지우지 않음(update 모드 보존).
- 호스트 독립: 순수 파이썬. plugin/skill/ZIP은 이 스크립트를 부르는 얇은 front door일 뿐.

사용:
    python3 init.py                         # 대화형(메뉴)
    python3 init.py --flavor codex --target ~/work/my-system --yes
    python3 init.py --flavor claude --target . --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"
FLAVORS = ("claude", "codex", "antigravity")
# 사용자 데이터 디렉토리 — 내용물은 절대 덮어쓰거나 지우지 않는다(.gitkeep만 보장).
PRESERVE_DIRS = ("tasks", "_local")
# scaffold-once 파일 — 신규 설치엔 정본을 깔되, 이미 있으면 사용자 설정이므로 보존(덮어쓰지 않음).
# 볼트 브리지 vault.config 는 볼트 경로·기본 도메인 같은 사용자 설정이라 update가 지우면 안 된다.
PRESERVE_IF_EXISTS = ("_shared/vault.config",)

# flavor별 지침파일(에이전트가 자동 로드) — validate.py FLAVOR['instruction']과 일치해야.
INSTRUCTION_FILE = {"claude": "CLAUDE.md", "codex": "AGENTS.md", "antigravity": "AGENTS.md"}
# knot 자동층(--with-knot): 고정 스니펫을 대상 지침파일에만 주입. 마커로 멱등 재생성·제거 가능.
KNOT_BLOCK = SCRIPT_DIR / "knot_block.md"
KNOT_START, KNOT_END = "<!-- knot:start -->", "<!-- knot:end -->"
# goal 요금가드(--with-guard): opt-in 가드 *배선*만 주입(정책은 coach=usage-coach 단일정본).
# 결정성 유지 — 고정 정본 파일을 결정적으로 복사/병합할 뿐 모델 창작 없음(knot과 동일 부류).
GUARD_DIR = SCRIPT_DIR / "guard"
GUARD_HOOK_MARKER = "coach --hook"   # claude settings.json Stop 항목 식별자(멱등 dedup용)
# knot 능동 스킬은 플러그인 최상위 skills/knot/ 로 배포된다(configure-multiagent와 동일하게
# 호스트가 네이티브 로드). 워크스페이스로 복사하지 않는다 — agy는 워크스페이스 스킬을 스캔하지
# 않고 글로벌 플러그인 스킬만 로드하므로(검증: gemini가 가용 스킬 목록에 knot 확인). claude/codex도
# 플러그인 스킬로 동일하게 로드된다. --with-knot은 passive 관리블록(자동층) 주입만 담당.


def available_flavors() -> list[str]:
    return [f for f in FLAVORS if (TEMPLATES_DIR / f).is_dir()]


def choose_flavor(arg: str | None, flavors: list[str]) -> str:
    if arg:
        if arg not in flavors:
            sys.exit(f"[error] unknown flavor '{arg}'. available: {', '.join(flavors)}")
        return arg
    print("어떤 멀티에이전트 시스템을 구성할까요?")
    for i, f in enumerate(flavors, 1):
        print(f"  {i}. {f}")
    while True:
        sel = input("선택 [번호]: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(flavors):
            return flavors[int(sel) - 1]
        print("  잘못된 선택")


def choose_target(arg: str | None, flavor: str) -> Path:
    if arg:
        return Path(arg).expanduser().resolve()
    default = str(Path.cwd() / f"multi-agent-{flavor}")
    raw = input(f"설치할 폴더 [{default}]: ").strip() or default
    return Path(raw).expanduser().resolve()


def guard_target(target: Path, template_dir: Path) -> None:
    """installer 자기 자신/템플릿 트리 안에 설치하는 사고 방지."""
    bad = [SCRIPT_DIR, template_dir]
    for b in bad:
        if target == b or b in target.parents or target in b.parents:
            sys.exit(f"[error] installer/template 트리 안에는 설치할 수 없습니다: {target}")


def is_user_data(rel: Path) -> bool:
    """tasks/ · _local/ 하위의 .gitkeep 외 파일 = 사용자 데이터(건드리지 않음)."""
    return len(rel.parts) >= 1 and rel.parts[0] in PRESERVE_DIRS and rel.name != ".gitkeep"


def copy_template(template_dir: Path, target: Path, dry: bool) -> tuple[list[Path], list[Path]]:
    """템플릿 파일을 target에 복사. target-only 파일(사용자 tasks/ 작업물)은
    삭제하지 않으므로 update 모드에서 자동 보존된다.
    (written, preserved) 반환 — preserved는 이미 존재해 건너뛴 scaffold-once 사용자 설정."""
    written: list[Path] = []
    preserved: list[Path] = []
    for src in sorted(template_dir.rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(template_dir)
        if is_user_data(rel):  # 방어적: 템플릿엔 .gitkeep만 있어 보통 도달 안 함
            continue
        dest = target / rel
        # scaffold-once: 사용자 설정 파일이 이미 있으면 보존(update가 덮어쓰지 않음). 신규면 정본 기록.
        if rel.as_posix() in PRESERVE_IF_EXISTS and dest.exists():
            preserved.append(rel)
            continue
        if not dry:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        written.append(rel)
    return written, preserved


def inject_knot(target: Path, flavor: str, dry: bool) -> str:
    """대상 지침파일에 고정 knot 블록을 주입(멱등). 마커가 있으면 그 사이를 교체,
    없으면 말미에 append. 루트/templates는 절대 건드리지 않음 — target 폴더 한정.
    init.py의 결정성 유지: 모델 창작 없이 knot_block.md 그대로 삽입."""
    block = KNOT_BLOCK.read_text(encoding="utf-8").strip("\n")
    instr = target / INSTRUCTION_FILE[flavor]
    text = instr.read_text(encoding="utf-8") if instr.is_file() else ""
    if KNOT_START in text and KNOT_END in text:
        new = re.sub(re.escape(KNOT_START) + r".*?" + re.escape(KNOT_END),
                     block, text, count=1, flags=re.S)
        action = "교체"
    else:
        new = text.rstrip("\n") + "\n\n" + block + "\n"
        action = "추가"
    if not dry:
        instr.write_text(new, encoding="utf-8")
    return f"knot 블록 {action} → {INSTRUCTION_FILE[flavor]}"


def _claude_settings_with_guard(existing: str, entry: dict) -> str:
    """기존 settings.json(없으면 빈 dict)에 guard Stop 항목을 멱등 병합.
    사용자가 손수 넣은 다른 Stop 훅은 보존, guard 항목(마커)만 dedup 후 정본으로 교체."""
    try:
        data = json.loads(existing) if existing.strip() else {}
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        hooks = data["hooks"] = {}
    stop = hooks.get("Stop")
    if not isinstance(stop, list):
        stop = hooks["Stop"] = []
    stop[:] = [e for e in stop if GUARD_HOOK_MARKER not in json.dumps(e, ensure_ascii=False)]
    stop.append(entry)
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def inject_guard(target: Path, flavor: str, dry: bool) -> str:
    """opt-in goal 요금가드 *배선*을 대상에 주입(멱등). 정책은 coach(usage-coach) 단일정본.
    claude = .claude/settings.json Stop 훅(coach --hook) / codex = _shared/guard/ 워처 복사 /
    antigravity = no-op(agy /goal 루프 없음). init.py 결정성 유지(고정 정본 복사·병합만)."""
    if flavor == "antigravity":
        return "guard 미지원(agy /goal 자율 루프 없음) — 변경 없음(다음 버전)"
    if flavor == "claude":
        entry = json.loads((GUARD_DIR / "claude_hook.json").read_text(encoding="utf-8"))
        dest = target / ".claude" / "settings.json"
        existing = dest.read_text(encoding="utf-8") if dest.is_file() else ""
        text = _claude_settings_with_guard(existing, entry)
        if not dry:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
        return "guard Stop 훅 주입 → .claude/settings.json (coach --hook)"
    # codex
    out = target / "_shared" / "guard"
    for name in ("codex_goal_watch.mjs", "README.md"):
        if not dry:
            out.mkdir(parents=True, exist_ok=True)
            shutil.copy2(GUARD_DIR / name, out / name)
    return "guard 워처 복사 → _shared/guard/ (codex_goal_watch.mjs)"


def main() -> None:
    ap = argparse.ArgumentParser(description="MultiAgent 시스템 생성기 (결정적 스캐폴더)")
    ap.add_argument("--flavor", choices=FLAVORS, help="claude | codex | antigravity (생략 시 메뉴)")
    ap.add_argument("--target", help="설치 대상 폴더 (생략 시 질문)")
    ap.add_argument("--yes", action="store_true", help="확인 프롬프트 생략")
    ap.add_argument("--no-validate", action="store_true", help="설치 후 validate 건너뜀")
    ap.add_argument("--with-knot", action="store_true",
                    help="지침파일에 knot 지식 vault 관리블록 주입(선택, $KNOT_VAULT 게이트)")
    ap.add_argument("--with-guard", action="store_true",
                    help="opt-in goal 요금가드 배선 주입(선택, claude=Stop훅 / codex=워처. 런타임 on/off=coach guard)")
    ap.add_argument("--dry-run", action="store_true", help="실제 쓰지 않고 미리보기")
    args = ap.parse_args()

    flavors = available_flavors()
    if not flavors:
        sys.exit(f"[error] 템플릿이 없습니다: {TEMPLATES_DIR}")

    flavor = choose_flavor(args.flavor, flavors)
    template_dir = TEMPLATES_DIR / flavor
    target = choose_target(args.target, flavor)
    guard_target(target, template_dir)

    mode = "update" if (target.exists() and any(target.iterdir())) else "init"
    print()
    print(f"  flavor : {flavor}")
    print(f"  target : {target}")
    print(f"  mode   : {mode}  (update=시스템 파일만 갱신, tasks/·_local/ 사용자 데이터 보존)")
    if args.dry_run:
        print("  [dry-run] 실제 변경 없음")

    if not args.yes and not args.dry_run:
        if input("\n진행할까요? [y/N]: ").strip().lower() not in ("y", "yes"):
            sys.exit("취소됨")

    written, preserved = copy_template(template_dir, target, dry=args.dry_run)
    prefix = "(dry) " if args.dry_run else ""
    print(f"\n  {prefix}{len(written)}개 파일 {'복사 예정' if args.dry_run else '복사 완료'}.")
    if preserved:
        names = ", ".join(p.as_posix() for p in preserved)
        print(f"  {prefix}{len(preserved)}개 사용자 설정 보존(scaffold-once, 덮어쓰지 않음): {names}")

    if args.with_knot:
        print(f"  {prefix}{inject_knot(target, flavor, dry=args.dry_run)}")

    if args.with_guard:
        print(f"  {prefix}{inject_guard(target, flavor, dry=args.dry_run)}")

    validate = SCRIPT_DIR / "validate.py"
    if not args.no_validate and not args.dry_run and validate.exists():
        print("\n  validate.py 실행...")
        rc = subprocess.run(
            [sys.executable, str(validate), "--flavor", flavor, "--target", str(target)]
        ).returncode
        if rc != 0:
            sys.exit(f"[warn] validate가 문제를 보고했습니다 (exit {rc})")

    print(f"\n  완료. 다음: cd {target} 후 해당 도구({flavor}) 실행.")


if __name__ == "__main__":
    main()
