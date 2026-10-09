#!/bin/sh
# Shared project status for terminal tabs (Pi extension and Claude Code hooks).
#   agent-status.sh start|stop <agent> <pid> <project-dir> [tty]
# Each agent records "<status> <pid> <agent>" in a file named after its tty under
# a per-project state directory. On every change the script counts the live
# agents of the project and writes the combined title to all of their tabs, so
# the PyCharm project tab shows "working" while at least one agent works.
# Overrides for tests: AGENT_STATUS_STATE_DIR, AGENT_STATUS_DEV_DIR.

action=$1 agent=$2 pid=$3 project=$4 tty=$5
case "$action" in start) status=working ;; stop) status=done ;; *) exit 0 ;; esac
[ -n "$agent" ] && [ -n "$pid" ] && [ -n "$project" ] || exit 0
[ -n "$tty" ] || tty=$(ps -o tty= -p "$pid" 2>/dev/null | tr -d ' ')
case "$tty" in ""|"??") exit 0 ;; esac
tty=${tty#/dev/}

dev_dir=${AGENT_STATUS_DEV_DIR:-/dev}
root=$(git -C "$project" rev-parse --show-toplevel 2>/dev/null) || root=$project
key=$(printf '%s' "$root" | shasum | cut -c1-16)
state=${AGENT_STATUS_STATE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/agent-sound-notifier}/$key
mkdir -p "$state" || exit 0

tmp=$(mktemp "$state/.entry.XXXXXX") || exit 0
printf '%s %s %s\n' "$status" "$pid" "$agent" > "$tmp" && mv "$tmp" "$state/$tty"

working=0 done=0
for entry in "$state"/*; do
  [ -f "$entry" ] || continue
  read -r s p a < "$entry"
  if ! kill -0 "$p" 2>/dev/null; then rm -f "$entry"; continue; fi
  case "$s" in working) working=$((working + 1)) ;; done) done=$((done + 1)) ;; esac
done

total=$((working + done))
if [ "$working" -gt 0 ] && [ "$done" -gt 0 ]; then summary="⚪ $working arbeitet · 🟡 $done fertig"
elif [ "$working" -gt 0 ]; then summary="⚪ $working arbeitet"
else summary="🟡 $done fertig"
fi

for entry in "$state"/*; do
  [ -f "$entry" ] || continue
  read -r s p a < "$entry"
  if [ "$total" -gt 1 ]; then
    case "$s" in working) own="⚪" ;; *) own="🟡" ;; esac
    title="$summary · hier $own $a"
  else
    title="$summary · $a"
  fi
  device="$dev_dir/${entry##*/}"
  [ -w "$device" ] && printf '\033]0;%s\007' "$title" > "$device" 2>/dev/null
done
exit 0
