#!/bin/sh
# Claude Code hook: mirrors the Pi extension.
#   start (UserPromptSubmit) -> project status "working" in the tab titles
#   stop  (Stop)             -> project status "done" + completion sound
#   ask   (PreToolUse AskUserQuestion|ExitPlanMode)
#                            -> same as stop: Claude waits for an answer mid-turn,
#                               so Stop does not fire; PostToolUse runs "start" again
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

# Windows (Claude Code runs hooks in Git Bash): no terminal devices, so no tab
# status; only the completion sound via PowerShell. macOS continues below.
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*)
    case "$1" in
      stop|ask)
        powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -Command \
          "\$f = Join-Path \$env:WINDIR 'Media\\Windows Notify System Generic.wav'; if (Test-Path \$f) { (New-Object Media.SoundPlayer \$f).PlaySync() } else { [System.Media.SystemSounds]::Asterisk.Play(); Start-Sleep -Milliseconds 800 }"
        ;;
    esac
    exit 0
    ;;
esac

case "$1" in
  start) set_status start ;;
  stop|ask)
    set_status stop
    /usr/bin/afplay -v 0.5 /System/Library/Sounds/Pop.aiff
    ;;
esac
exit 0
