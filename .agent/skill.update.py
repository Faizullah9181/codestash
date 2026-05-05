#!/usr/bin/env python3
"""
skill.update.py — Skill maintenance utility for .agent/skills/

Commands:
  list              List all skills with name and version
  check             Validate frontmatter for all skills (name + description required)
  bump <skill>      Bump the patch version of a specific skill (e.g. 1.2.3 → 1.2.4)
  sync <src> <dst>  Copy all .md files from src/references/ into dst/references/
                    as upstream-*.md (preserves originals)
"""

import re
import shutil
import sys
from pathlib import Path

SKILLS_DIR = Path(__file__).parent
REQUIRED_FRONTMATTER_KEYS = {"name", "description"}


# ── helpers ──────────────────────────────────────────────────────────────────

def _parse_frontmatter(text: str) -> dict[str, str]:
    """Return key→value dict for the first YAML frontmatter block, or {}."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


def _skill_dirs() -> list[Path]:
    if not SKILLS_DIR.exists():
        return []
    return sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())


def _skill_md(skill_dir: Path) -> Path:
    return skill_dir / "SKILL.md"


# ── commands ─────────────────────────────────────────────────────────────────

def cmd_list() -> None:
    """Print a table of skill name, version, and file path."""
    dirs = _skill_dirs()
    if not dirs:
        print("No skills found in", SKILLS_DIR)
        return

    rows: list[tuple[str, str, str]] = []
    for d in dirs:
        md = _skill_md(d)
        if not md.exists():
            rows.append((d.name, "(no SKILL.md)", str(md.relative_to(SKILLS_DIR.parent))))
            continue
        fm = _parse_frontmatter(md.read_text())
        name = fm.get("name", d.name)
        version = fm.get("version", "—")
        rows.append((name, version, str(md.relative_to(SKILLS_DIR.parent))))

    col_w = [max(len(r[i]) for r in rows + [("Skill", "Version", "File")]) for i in range(3)]
    header = f"{'Skill':<{col_w[0]}}  {'Version':<{col_w[1]}}  File"
    print(header)
    print("-" * len(header))
    for name, version, path in rows:
        print(f"{name:<{col_w[0]}}  {version:<{col_w[1]}}  {path}")


def cmd_check() -> int:
    """Validate frontmatter for every skill. Returns exit code."""
    dirs = _skill_dirs()
    if not dirs:
        print("No skills found in", SKILLS_DIR)
        return 0

    errors = 0
    for d in dirs:
        md = _skill_md(d)
        if not md.exists():
            print(f"  MISSING  {d.name}: SKILL.md not found")
            errors += 1
            continue
        fm = _parse_frontmatter(md.read_text())
        missing = REQUIRED_FRONTMATTER_KEYS - fm.keys()
        if missing:
            print(f"  FAIL     {d.name}: missing frontmatter key(s): {', '.join(sorted(missing))}")
            errors += 1
        else:
            print(f"  OK       {d.name}  (v{fm.get('version', '?')})")

    if errors:
        print(f"\n{errors} skill(s) failed validation.")
    else:
        print(f"\nAll {len(dirs)} skill(s) passed.")
    return errors


def cmd_bump(skill_name: str) -> int:
    """Bump patch version of <skill_name> in its SKILL.md frontmatter."""
    target = SKILLS_DIR / skill_name
    if not target.exists():
        # try case-insensitive match
        matches = [d for d in _skill_dirs() if d.name.lower() == skill_name.lower()]
        if not matches:
            print(f"Error: no skill directory found for '{skill_name}'")
            print("Available skills:", ", ".join(d.name for d in _skill_dirs()))
            return 1
        target = matches[0]

    md = _skill_md(target)
    if not md.exists():
        print(f"Error: {md} not found")
        return 1

    text = md.read_text()
    fm = _parse_frontmatter(text)
    current = fm.get("version", "0.0.0")

    # Parse and bump patch
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", current)
    if not match:
        print(f"Error: cannot parse version '{current}' — expected MAJOR.MINOR.PATCH")
        return 1

    major, minor, patch = match.groups()
    new_version = f"{major}.{minor}.{int(patch) + 1}"

    updated = text.replace(f"version: {current}", f"version: {new_version}", 1)
    if updated == text:
        print(f"Warning: 'version: {current}' not found in frontmatter — no change made")
        return 1

    md.write_text(updated)
    print(f"Bumped {target.name}: {current} → {new_version}")
    return 0


def cmd_sync(src: str, dst: str) -> int:
    """Copy .md files from src/references/ into dst/references/ as upstream-*.md"""
    src_refs = Path(src).expanduser().resolve() / "references"
    dst_refs = Path(dst).expanduser().resolve() / "references"

    if not src_refs.exists():
        print(f"Error: source references directory not found: {src_refs}")
        return 1

    dst_refs.mkdir(parents=True, exist_ok=True)
    copied = 0
    for md_file in sorted(src_refs.glob("*.md")):
        dest_name = f"upstream-{md_file.name}"
        dest = dst_refs / dest_name
        shutil.copy2(md_file, dest)
        print(f"  copied {md_file.name} → {dest.relative_to(Path.cwd())}")
        copied += 1

    if copied == 0:
        print(f"No .md files found in {src_refs}")
        return 1

    print(f"\nSynced {copied} file(s) as upstream-* into {dst_refs}")
    return 0


# ── entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    command = args[0].lower()

    if command == "list":
        cmd_list()

    elif command == "check":
        sys.exit(cmd_check())

    elif command == "bump":
        if len(args) < 2:
            print("Usage: skill.update.py bump <skill-name>")
            sys.exit(1)
        sys.exit(cmd_bump(args[1]))

    elif command == "sync":
        if len(args) < 3:
            print("Usage: skill.update.py sync <src-skill-dir> <dst-skill-dir>")
            sys.exit(1)
        sys.exit(cmd_sync(args[1], args[2]))

    else:
        print(f"Unknown command: '{command}'")
        print("Run with --help for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
