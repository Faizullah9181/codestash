#!/usr/bin/env python3
"""
skill.update.py — Skill maintenance utility for .agent/skills/

Commands:
  list              List all skills with name and version
  check             Validate frontmatter for all skills (name + description required)
  bump <skill>      Bump the patch version of a specific skill (e.g. 1.2.3 → 1.2.4)
  sync <src> <dst>  Copy all .md files from src/references/ into dst/references/
                    as upstream-*.md (preserves originals)
  add <github-url>  Download a skill from a GitHub URL and save it locally.
                    The URL should point to a skill directory, e.g.:
                    https://github.com/fastapi/fastapi/tree/master/fastapi/.agents/skills/fastapi
  sync              Sync (import) all skills from .agent/skills.json.
                    Downloads SKILL.md and reference files for each entry.
                    No parameters needed — sources in skills.json are GitHub URLs.
"""

import json
import re
import shutil
import sys
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

SKILLS_DIR = Path(__file__).parent / "skills"
SKILLS_JSON = SKILLS_DIR.parent / "skills.json"
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


# ── network helpers ────────────────────────────────────────────────────────────


def _fetch_url(url: str, timeout: int = 15) -> str:
    """Fetch a URL and return the response body as text."""
    req = urllib.request.Request(url, headers={"User-Agent": "skill.update.py/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def _github_url_to_raw(
    github_url: str, filepath: str = "SKILL.md", branch: str = "master"
) -> str:
    """Convert a GitHub tree URL to a raw.githubusercontent.com URL.

    Handles these formats:
      https://github.com/owner/repo/tree/branch/path/to/skill
      https://github.com/owner/repo/blob/branch/path/to/skill/SKILL.md
    """
    parsed = urllib.parse.urlparse(github_url)
    parts = parsed.path.strip("/").split("/")

    if len(parts) < 5:
        raise ValueError(f"Cannot parse GitHub URL: {github_url}")

    owner = parts[0]
    repo = parts[1]
    # parts[2] is "tree" or "blob"
    ref = parts[3]
    skill_path = "/".join(parts[4:])

    # If the URL points to a file (blob), use its directory
    if parts[2] == "blob":
        skill_path = "/".join(parts[4:-1])

    return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{skill_path}/{filepath}"


def _resolve_skillsmp_to_github(source_url: str) -> str | None:
    """Resolve a skillsmp.com URL to the GitHub repo URL.

    Fetches the page and extracts the githubUrl from embedded JSON-LD data.
    """
    try:
        html = _fetch_url(source_url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        print(f"  Warning: could not fetch {source_url}")
        return None

    # Try to find githubUrl in the RSC/embedded data
    # Pattern: "githubUrl":"https://github.com/..."
    match = re.search(r'"githubUrl"\s*:\s*"([^"]+)"', html)
    if match:
        return match.group(1)

    # Fallback: find the canonical codeRepository in JSON-LD
    match = re.search(r'"codeRepository"\s*:\s*"([^"]+)"', html)
    if match:
        return match.group(1)

    return None


def _extract_sanitized_github_url(github_url: str) -> str | None:
    """Extract and sanitize the GitHub URL, removing trailing escapes."""
    if not github_url:
        return None
    # Remove any trailing backslash escapes or whitespace
    github_url = github_url.rstrip("\\").strip()
    # Ensure it starts with https://github.com
    if not github_url.startswith("https://github.com/"):
        return None
    return github_url


def _get_default_branch(owner: str, repo: str) -> str:
    """Query the GitHub API for the default branch name."""
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        data = json.loads(_fetch_url(url))
        return data.get("default_branch", "main")
    except Exception:
        return "main"


def _download_skill(
    github_url: str, skill_name: str | None = None, description: str | None = None
) -> int:
    """Download a SKILL.md (and references/) from a GitHub skill directory.

    Args:
        github_url: GitHub URL pointing to the skill directory.
                    e.g. https://github.com/fastapi/fastapi/tree/master/fastapi/.agents/skills/fastapi
        skill_name: Override name for the skill (defaults to directory name from URL).
        description: Description to inject into frontmatter if missing.

    Returns:
        0 on success, 1 on error.
    """
    # Derive skill name from last path segment if not provided
    if not skill_name:
        parts = github_url.rstrip("/").split("/")
        skill_name = parts[-1]

    skill_dir = SKILLS_DIR / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Downloading skill '{skill_name}' from {github_url}")

    # Parse GitHub URL parts
    parsed = urllib.parse.urlparse(github_url)
    path_parts = parsed.path.strip("/").split("/")

    if len(path_parts) < 5 or path_parts[2] not in ("tree", "blob"):
        print(f"  Error: invalid GitHub URL format: {github_url}")
        print("  Expected: https://github.com/owner/repo/tree/branch/path/to/skill")
        return 1

    owner = path_parts[0]
    repo = path_parts[1]
    ref = path_parts[3]
    skill_subdir = "/".join(path_parts[4:])
    if path_parts[2] == "blob":
        # Strip the filename, keep directory
        skill_subdir = "/".join(path_parts[4:-1])

    # 1. Download SKILL.md
    skill_md_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{skill_subdir}/SKILL.md"
    print("    fetching SKILL.md...")
    try:
        content = _fetch_url(skill_md_url)
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        print(f"  Error: could not download SKILL.md from {skill_md_url}: {e}")
        return 1

    # Ensure frontmatter has name and description
    if not content.startswith("---"):
        # No frontmatter — add one
        fm_lines = ["---", f"name: {skill_name}"]
        if description:
            fm_lines.append(f"description: {description}")
        else:
            fm_lines.append(
                f"description: {skill_name} skill imported from {owner}/{repo}"
            )
        fm_lines.append("---")
        content = "\n".join(fm_lines) + "\n\n" + content
    else:
        # Has frontmatter — ensure name matches
        fm = _parse_frontmatter(content)
        if "name" not in fm:
            # Inject name after opening ---
            content = content.replace("---\n", f"---\nname: {skill_name}\n", 1)
        elif fm.get("name") != skill_name:
            # Update name to match directory
            content = content.replace(f"name: {fm['name']}", f"name: {skill_name}", 1)

        if description and "description" not in fm:
            # Inject description
            name_line = f"name: {skill_name}\n"
            content = content.replace(
                name_line, f"{name_line}description: {description}\n", 1
            )

    (skill_dir / "SKILL.md").write_text(content)
    print(f"    ✓ wrote {skill_dir / 'SKILL.md'}")

    # 2. Download references/ directory (if exists)
    # List files via GitHub API
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{skill_subdir}/references?ref={ref}"
    try:
        refs_json = json.loads(_fetch_url(api_url))
        if isinstance(refs_json, list):
            refs_dir = skill_dir / "references"
            refs_dir.mkdir(exist_ok=True)
            for entry in refs_json:
                if entry.get("type") == "file" and entry.get("name", "").endswith(
                    ".md"
                ):
                    ref_name = entry["name"]
                    ref_url = entry["download_url"]
                    print(f"    fetching references/{ref_name}...")
                    try:
                        ref_content = _fetch_url(ref_url)
                        (refs_dir / ref_name).write_text(ref_content)
                        print(f"    ✓ wrote references/{ref_name}")
                    except (urllib.error.HTTPError, urllib.error.URLError):
                        print(f"    ⚠ could not download references/{ref_name}")
    except (urllib.error.HTTPError, urllib.error.URLError):
        # No references directory — that's fine
        pass
    except (json.JSONDecodeError, KeyError):
        pass

    print(f"  ✓ Skill '{skill_name}' imported successfully!")
    return 0


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
            rows.append(
                (d.name, "(no SKILL.md)", str(md.relative_to(SKILLS_DIR.parent)))
            )
            continue
        fm = _parse_frontmatter(md.read_text())
        name = fm.get("name", d.name)
        version = fm.get("version", "—")
        rows.append((name, version, str(md.relative_to(SKILLS_DIR.parent))))

    col_w = [
        max(len(r[i]) for r in rows + [("Skill", "Version", "File")]) for i in range(3)
    ]
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
            print(
                f"  FAIL     {d.name}: missing frontmatter key(s): {', '.join(sorted(missing))}"
            )
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
        print(
            f"Warning: 'version: {current}' not found in frontmatter — no change made"
        )
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


def cmd_add(
    github_url: str, skill_name: str | None = None, description: str | None = None
) -> int:
    """Add a skill from a GitHub URL."""
    github_url = _extract_sanitized_github_url(github_url) or github_url
    return _download_skill(github_url, skill_name=skill_name, description=description)


def cmd_import() -> int:
    """Import all skills listed in .agent/skills.json."""
    if not SKILLS_JSON.exists():
        print(f"Error: {SKILLS_JSON} not found")
        return 1

    with open(SKILLS_JSON) as f:
        skills = json.load(f)

    if not skills:
        print("No skills found in skills.json")
        return 0

    print(f"Found {len(skills)} skill(s) in skills.json\n")
    errors = 0

    for skill in skills:
        source = skill.get("source", "")
        slug = skill.get("slug", "")
        name = skill.get("name", slug.split("/")[-1] if "/" in slug else slug)
        description = skill.get("description", "")

        # Derive a filesystem-safe skill name from the slug
        # slug like "fastapi/fastapi" → use the last part
        fs_name = slug.split("/")[-1] if "/" in slug else slug
        # Sanitize for filesystem
        fs_name = re.sub(r"[^a-z0-9_-]", "-", fs_name.lower())

        print(f"→ Importing '{name}' (slug: {slug})")

        # Step 1: Resolve source URL to GitHub URL
        if "github.com" in source:
            github_url = source
        elif "skillsmp.com" in source:
            github_url = _resolve_skillsmp_to_github(source)
            if not github_url:
                print(f"  ⚠ Could not resolve {source} to a GitHub URL — skipping\n")
                errors += 1
                continue
            github_url = _extract_sanitized_github_url(github_url) or github_url
            print(f"  Resolved to: {github_url}")
        else:
            print(f"  ⚠ Unsupported source URL format: {source} — skipping\n")
            errors += 1
            continue

        # Step 2: Download
        rc = _download_skill(github_url, skill_name=fs_name, description=description)
        if rc != 0:
            errors += 1
        print()

    if errors:
        print(f"✗ {errors} skill(s) failed to import")
        return 1
    print("✓ Import complete!")
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
        if len(args) < 2:
            # No args: run import from skills.json
            sys.exit(cmd_import())
        # With args: backward compat — old sync <src> <dst> behavior
        if len(args) < 3:
            print("Usage: skill.update.py sync [src-skill-dir dst-skill-dir]")
            print("  No args  → import all skills from skills.json")
            print(
                "  With args → copy .md files from src/references/ into dst/references/"
            )
            sys.exit(1)
        sys.exit(cmd_sync(args[1], args[2]))

    elif command == "import":
        sys.exit(cmd_import())

    elif command == "add":
        if len(args) < 2:
            print("Usage: skill.update.py add <github-url> [skill-name] [description]")
            sys.exit(1)
        github_url = args[1]
        skill_name = args[2] if len(args) > 2 else None
        description = args[3] if len(args) > 3 else None
        sys.exit(cmd_add(github_url, skill_name=skill_name, description=description))

    else:
        print(f"Unknown command: '{command}'")
        print("Run with --help for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
