#!/usr/bin/env bash
set -euo pipefail

INPUT=$(cat)
COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
TOOL_NAME=$(printf '%s' "$INPUT" | jq -r '.tool_name // empty')

# Block destructive file system manipulation at the filesystem root.
if printf '%s' "$COMMAND" | grep -Eq '(^|[[:space:]])rm[[:space:]].*[[:space:]]/([[:space:]]|$)'; then
  printf '%s\n' '{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"CRITICAL SYSTEM VIOLATION: directory deletions at root are blocked."}}'
  exit 2
fi

# Bound naive Read calls so architecture audits prefer ast-grep or targeted slices.
if [[ "$TOOL_NAME" == "Read" ]]; then
  printf '%s\n' '{"hookSpecificOutput":{"permissionDecision":"allow","updatedInput":{"limit":500}}}'
  exit 0
fi

exit 0
