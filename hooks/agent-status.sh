#!/bin/sh
# Record local status for the PyCharm companion; keep the terminal's own title small.
# agent-status.sh start|stop <Pi|Claude> <pid> <project-dir> [tty]
action=$1 agent=$2 pid=$3 project=$4 tty=$5
case "$action" in start) status=working; dot="⚪" ;; stop) status=done; dot="🟡" ;; *) exit 0 ;; esac
case "$agent" in Pi|Claude) ;; *) exit 0 ;; esac
case "$pid" in ""|*[!0-9]*) exit 0 ;; esac
[ "$pid" -gt 1 ] && [ -n "$project" ] || exit 0
[ -n "$tty" ] || tty=$(ps -o tty= -p "$pid" 2>/dev/null | tr -d ' ')
tty=${tty#/dev/}
case "$tty" in ""|*[!a-zA-Z0-9_-]*) exit 0 ;; esac

dev_dir=${AGENT_STATUS_DEV_DIR:-/dev}
[ -w "$dev_dir/$tty" ] || exit 0
root=$(git -C "$project" rev-parse --show-toplevel 2>/dev/null) || root=$(cd "$project" 2>/dev/null && pwd -P) || exit 0
key=$(printf '%s' "$root" | shasum | cut -c1-16)
state=${AGENT_STATUS_STATE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/agent-sound-notifier}/$key
(umask 077; mkdir -p "$state") || exit 0

# Atomic replacement: the companion never reads partial status or project paths.
tmp=$(mktemp "$state/.project.XXXXXX") || exit 0
printf '%s\n' "$root" > "$tmp" && mv "$tmp" "$state/.project"
tmp=$(mktemp "$state/.entry.XXXXXX") || exit 0
printf '%s %s %s\n' "$status" "$pid" "$agent" > "$tmp" && mv "$tmp" "$state/$tty"

# Reap dead sessions; .project and in-flight writes aren't session entries.
for entry in "$state"/*; do
  [ -f "$entry" ] || continue
  read -r s p a < "$entry"
  case "$p" in ""|*[!0-9]*) continue ;; esac
  if ! kill -0 "$p" 2>/dev/null; then rm -f "$entry"; fi
done

# Only this terminal receives its own status. Project counts belong to the IDE.
printf '\033]0;%s %s\007' "$dot" "$agent" > "$dev_dir/$tty" 2>/dev/null
exit 0
