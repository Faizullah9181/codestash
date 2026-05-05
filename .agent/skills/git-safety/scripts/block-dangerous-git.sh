#!/usr/bin/env bash
# block-dangerous-git.sh
# Claude PreToolCall hook — blocks dangerous git commands.
# Exit 2 = block the tool call with the message printed to stdout.

set -euo pipefail

INPUT=$(cat)

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || true)

if [[ -z "$COMMAND" ]]; then
  exit 0
fi

DANGEROUS_PATTERNS=(
  "git push"
  "git reset --hard"
  "git clean -f"
  "git clean -fd"
  "git branch -D"
  "git checkout \."
  "git restore"
)

for PATTERN in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE "$PATTERN"; then
    echo "BLOCKED: dangerous git command detected: $COMMAND"
    echo "If you intended to run this, do it manually in your terminal."
    exit 2
  fi
done

exit 0
