#!/bin/sh
# Claude Code hook: mirrors the Pi extension.
#   start (UserPromptSubmit) -> project status "working" in the tab titles
#   stop  (Stop)             -> project status "done" + completion sound
# Hooks run without a controlling terminal, so the nearest ancestor process with
# a terminal (the `claude` CLI) identifies this agent and its tab.
# Claude Code's own title must be off: CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1.

find_agent() {
  pid=$PPID
  while [ -n "$pid" ] && [ "$pid" -gt 1 ]; do
    tty=$(ps -o tty= -p "$pid" | tr -d ' ')
    case "$tty" in
      ""|"??") pid=$(ps -o ppid= -p "$pid" | tr -d ' ') ;;
      *) echo "$pid $tty"; return 0 ;;
    esac
  done
  return 1
}

set_status() {
  agent=$(find_agent) || return 0
  "$(dirname "$0")/agent-status.sh" "$1" Claude "${agent% *}" "${CLAUDE_PROJECT_DIR:-$PWD}" "${agent#* }"
}

case "$1" in
  start) set_status start ;;
  stop)
    set_status stop
    /usr/bin/afplay -v 0.5 /System/Library/Sounds/Pop.aiff
    ;;
esac
exit 0
