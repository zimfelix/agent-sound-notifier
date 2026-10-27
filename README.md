# Agent Sound Notifier — Version 1.4

Small, independent add-ons for coding agents in the terminal. Pick any of the three:

| # | Feature | Agent | What you get | macOS | Windows |
|---|---|---|---|---|---|
| 1 | **Sound** | Claude Code, Pi | A short sound when the agent finishes or asks you something. On macOS also a ⚪/🟡 dot in the terminal-tab title (working / done). | ✅ sound + tab dot | ✅ sound only |
| 2 | **Status line** | Claude Code only | `~/project (main)` · tok/s · context usage (orange from 200k, red from 250k tokens) · `Opus 5.5 · medium` | ✅ | ✅ |
| 3 | **Output style** | Claude Code only | "Strukturiert": skimmable German answers with result-first reports, 🔺 terms, 🎯 corrections, 🔀 trade-offs, diagrams instead of walls of text. | ✅ | ✅ |

Pi: see [Sound](#1--sound) for its extension. Nothing is sent anywhere; no extra model requests.

```text
~/Code/my-project (main)
~92.3 tok/s  41.2%/1M  Ø ~104.2 tok/s                         Opus 5.5 · medium
```

## Quick install (for agents)

Tell your coding agent:

```text
Install https://github.com/zimfelix/agent-sound-notifier for Claude Code.
Follow the "Steps for the agent" section in its README.
```

### Steps for the agent

1. **Ask the user** which features to install: `sound`, `statusline`, `style` (or all three). Describe them with the table above.
2. **Clone** the repository to a permanent folder — the settings point to it, so do not use a temp folder:
   - macOS: `git clone https://github.com/zimfelix/agent-sound-notifier ~/agent-sound-notifier`
   - Windows: `git clone https://github.com/zimfelix/agent-sound-notifier "$env:USERPROFILE\agent-sound-notifier"`
3. **Check requirements:**
   - Python 3.9+: macOS `/usr/bin/python3 --version` (ships with the Xcode command line tools); Windows `py -3 --version`. If missing on Windows, ask the user before running `winget install -e --id Python.Python.3.12`.
   - Windows + sound: [Git for Windows](https://git-scm.com/download/win) (Claude Code runs hooks in Git Bash), check with `bash --version`.
4. **Run the installer** from the repository folder with the chosen flags (`--all`, or any of `--sound --statusline --style`):
   - macOS: `/usr/bin/python3 install.py --all`
   - Windows: `py -3 install.py --all`

   It backs up `~/.claude/settings.json` (`settings.json.bak-<time>`), changes only its own entries, and can be run again safely.
5. Tell the user to **start a new Claude Code session**. The status line appears at the bottom; the sound plays after the next answer.

Remove features with the same flags plus `--uninstall`, e.g. `py -3 install.py --all --uninstall`. Run `install.py` without flags in a terminal to be asked feature by feature.

## 1 · Sound

| Event | macOS | Windows |
|---|---|---|
| Agent finishes, or asks a question / plan approval | `Pop` at half volume + 🟡 tab dot | Windows notification sound |
| You send a prompt / answer the question | ⚪ tab dot | – |

**Claude Code** uses `hooks/claude-notify.sh` through hooks: `Stop`, plus `PreToolUse`/`PostToolUse` for `AskUserQuestion|ExitPlanMode` (those pause the turn without `Stop`), and on macOS `UserPromptSubmit` for the ⚪ dot. On macOS the installer also sets `CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1`, otherwise Claude Code overwrites the tab title. Tab dots work in PyCharm's terminal, Terminal.app and Warp. In the Claude desktop app there is no terminal, so only the sound plays.

**Pi** loads the same behaviour as an extension (`extensions/agent-sound-notifier.ts`). From the repository root: `pi install "$(pwd)"` (PowerShell: `pi install "$PWD"`), restart Pi, check with `pi list`.

**Windows notes:** tab dots and the PyCharm companion are macOS-only (Windows terminals have no terminal device the hooks could write to). `.gitattributes` keeps the shell scripts on LF line endings so Git Bash can run them. Quick check in Git Bash: `bash hooks/claude-notify.sh stop` should play the sound; if not, check that `powershell.exe` runs and system sounds are not muted.

### PyCharm project tabs (optional, macOS)

The agent integrations write status files under `~/.cache/agent-sound-notifier/`. A small local PyCharm plugin shows totals per project in the window title, e.g. `learning-sandbox 🟡 2/3 finished · ⚪ 1 running`, also for inactive project tabs. It polls once per second, reads no conversations, and sets `Settings → Tools → Terminal → Use application title as tab name → Always` (keep it on, or the tab dots disappear too).

Build against an installed PyCharm 2026.2 (build `262.*`) and its bundled JDK with `sh pycharm-plugin/build.sh`, then **Settings → Plugins → gear → Install Plugin from Disk…** and pick `pycharm-plugin/build/agent-project-status.zip`. For another installation set `PYCHARM_HOME` to its `Contents` folder and `JAVA_HOME` to a JDK 21+. Restart the IDE only when no agent is working.

## 2 · Status line

`statusline/statusline.py`, Python standard library only. Details, measurement and limits: [`statusline/README.md`](statusline/README.md).

## 3 · Output style

`output-style/strukturiert.md` is a Claude Code [output style](https://docs.claude.com/en/docs/claude-code/output-styles) written in German for the repository author's way of working. The installer copies it to `~/.claude/output-styles/` and sets `"outputStyle": "Strukturiert"`. Switch styles any time with `/output-style`. Edit your copy freely: reinstalling backs it up first, uninstalling leaves an edited copy in place.

## Manual setup

If you prefer to edit `~/.claude/settings.json` (Windows: `%USERPROFILE%\.claude\settings.json`) yourself, use absolute paths with forward slashes:

```json
{
  "env": { "CLAUDE_CODE_DISABLE_TERMINAL_TITLE": "1" },
  "hooks": {
    "UserPromptSubmit": [ { "hooks": [ { "type": "command", "command": "\"/path/to/agent-sound-notifier/hooks/claude-notify.sh\" start 2>/dev/null || true", "async": true } ] } ],
    "Stop": [ { "hooks": [ { "type": "command", "command": "\"/path/to/agent-sound-notifier/hooks/claude-notify.sh\" stop 2>/dev/null || true", "async": true } ] } ],
    "PreToolUse": [ { "matcher": "AskUserQuestion|ExitPlanMode", "hooks": [ { "type": "command", "command": "\"/path/to/agent-sound-notifier/hooks/claude-notify.sh\" ask 2>/dev/null || true", "async": true } ] } ],
    "PostToolUse": [ { "matcher": "AskUserQuestion|ExitPlanMode", "hooks": [ { "type": "command", "command": "\"/path/to/agent-sound-notifier/hooks/claude-notify.sh\" start 2>/dev/null || true", "async": true } ] } ]
  },
  "statusLine": { "type": "command", "command": "/usr/bin/python3 /path/to/agent-sound-notifier/statusline/statusline.py" },
  "outputStyle": "Strukturiert"
}
```

On Windows keep only `Stop` and `PreToolUse`, prefix the hook commands with `bash` (`bash \"C:/Users/you/agent-sound-notifier/hooks/claude-notify.sh\" stop ...`), drop the `env` entry, and use your Python for the status line (`py -3 C:/Users/you/agent-sound-notifier/statusline/statusline.py`). For the output style, copy `output-style/strukturiert.md` to `~/.claude/output-styles/`.

## Development

`npm install`, `npm test`, `npm run typecheck` (Pi extension and status script); `python3 -m unittest -v tests/test_install.py` (installer); `cd statusline && python3 -m unittest -v test_statusline.py`; `sh pycharm-plugin/test.sh` and `sh pycharm-plugin/build.sh` (companion). The installer tests use a temporary config folder and never touch `~/.claude`.
