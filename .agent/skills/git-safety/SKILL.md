---
name: git-safety
description: Installs a git pre-tool-call hook that blocks dangerous git commands — push, reset --hard, clean -f/-fd, branch -D, checkout ./restore — from running without confirmation. Use when the user wants to prevent accidental destructive git operations, or when asked to set up git safety guards.
---

# Git Guardrails

Block dangerous git commands from running in agent sessions without explicit confirmation.

Blocked commands:
- `git push` (all variants, including `--force`)
- `git reset --hard`
- `git clean -f` / `git clean -fd`
- `git branch -D`
- `git checkout .` / `git restore`

## Setup

### 1. Confirm scope

Ask the user: **project-level or global?**

- **Project-level** — creates the hook in `.agent/hooks/` (only this repo)
- **Global** — creates the hook in a shared location and registers it in global agent settings

### 2. Copy the script

Copy `scripts/block-dangerous-git.sh` from this skill to:

- Project: `.agent/hooks/block-dangerous-git.sh`
- Global: `~/.agent/hooks/block-dangerous-git.sh`

Make it executable: `chmod +x <path>/block-dangerous-git.sh`

### 3. Register the hook

Add to `settings.json` (project: `.agent/settings.json`, global: `~/.agent/settings.json`):

```json
{
  "hooks": {
    "PreToolCall": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "<path>/block-dangerous-git.sh"
          }
        ]
      }
    ]
  }
}
```

Replace `<path>` with the absolute path to the script.

### 4. Verify

Run `git push` in a test prompt. The hook should block it with a `BLOCKED` message.
