# Claude Code status line

Feature 2 of this repository, usable without the sound feature. Install it with `install.py --statusline` from the repository root (see the [main README](../README.md)), or add it to `~/.claude/settings.json` yourself:

```json
{ "statusLine": { "type": "command", "command": "/usr/bin/python3 /path/to/agent-sound-notifier/statusline/statusline.py" } }
```

Python 3.9+ standard library only (macOS: `/usr/bin/python3`, Windows: `py -3`); no background service, no extra model requests.

```text
~/Code/my-project (main)
~92.3 tok/s  41.2%/1M  Ø ~104.2 tok/s                         Opus 5.5 · high
```

Left: rate of the last finished answer, context used / window size, chat average. The context turns **orange from 200,000 used tokens** and **red from 250,000** (absolute tokens = percent × window size, so the same for 200k and 1M windows) as a reminder to start a fresh session. Thresholds: `WARN_TOKENS` / `ALERT_TOKENS` in `statusline.py`. Right: model name and effort level from Claude Code's status line JSON (`model.display_name`, `effort.level`); without an effort field only the name.

## Measurement and limits

**No live value while streaming.** Claude Code does not pass stream tokens to the status line; the transcript only gets an entry per finished answer block. The left value is therefore the rate of the last answer once it is written.

Per answer (`message.id`): output tokens divided by the time from the previous main-conversation entry (prompt, tool result) to the last written block of that answer. This includes the wait for the first token, hence `~`. `Ø` is time-weighted: sum of output tokens / sum of these durations; your own waiting and tool run time do not count. Subagent (sidechain) entries are excluded.

New complete transcript lines are read incrementally. Without data it shows `— tok/s`. Right alignment uses the terminal width from `/dev/tty` (Windows: `CONOUT$`), otherwise `COLUMNS`, minus 5 columns (Claude Code indents the line and would otherwise cut it with "…"); without either, the model follows after two spaces. In a narrow terminal the model gets its own line. The branch is read directly from `.git/HEAD` (also worktrees), without calling `git`.

The script reads the local transcript only to count tokens and sends nothing. Its cache under `~/.claude/statusline-minimal/cache/` holds only message IDs, timestamps, token counts and file offsets, no prompts or answers. It can be deleted while Claude Code is closed.

## Tests and removal

`cd statusline && python3 -m unittest -v test_statusline.py` — seven tests with artificial data (colour thresholds and unchanged alignment, layout and weighted average, alignment and narrow fallback, partial lines, missing data, truncated transcript, path with branch and model without effort).

Remove it with `install.py --statusline --uninstall`, or delete the `statusLine` entry from `~/.claude/settings.json`. The status line belongs to Claude Code, not to the terminal: it looks the same in Warp, Terminal.app, Windows Terminal and the PyCharm or VS Code terminal.
