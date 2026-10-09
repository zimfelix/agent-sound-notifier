# Agent Sound Notifier — Version 1.1.0

Plays a short macOS sound and marks the terminal tab (e.g. in PyCharm) with a yellow dot when a coding agent finishes, so you notice it without watching the terminal. While the agent is working, the tab shows a neutral dot. It is independent of the model/provider.

Supported agents:

- **[Pi](https://github.com/earendil-works/pi)** — as a Pi extension (`extensions/agent-sound-notifier.ts`).
- **Claude Code** — as hooks (`hooks/claude-notify.sh`), see [Claude Code](#claude-code).

## Pi

From the repository root, install it for your Pi sessions:

```sh
pi install "$(pwd)"
```

Restart Pi, then confirm the package is listed with `pi list`. It will be available in any project. Remove it with `pi remove "$(pwd)"` from this repository.

### Notifications

- Listen for Pi's final `agent_settled` event and play the macOS `Pop` sound at reduced volume.
- Show a neutral dot while Pi is working and a yellow dot in the terminal-tab title when it settles.
- Keep each coding terminal small: `⚪ Pi` / `🟡 Pi` or `⚪ Claude` / `🟡 Claude`. White means running; yellow means the last response finished. There is no read/acknowledgement tracking.
- Show separate project totals through the [PyCharm companion](#pycharm-project-tabs): `🟡 2/3 finished · ⚪ 1 running`, `🟡 3/3 finished`, or `⚪ 3 running`. Finished means completed responses in still-live sessions; exited agents drop out. Projects are grouped by Git root, otherwise working directory.

The agent integrations write terminal titles via OSC and local status files under `~/.cache/agent-sound-notifier/` (see `hooks/agent-status.sh`). **OSC titles alone do not reliably refresh inactive PyCharm project tabs**; the companion updates native window titles independently of terminal selection. The full live smoke test after installing the companion is still pending.

## Claude Code

Claude Code does not load Pi extensions. The same behaviour is available there through two hooks that run `hooks/claude-notify.sh`: `UserPromptSubmit` sets a neutral dot in the terminal-tab title, `Stop` sets the yellow dot and plays the sound. Add them to `~/.claude/settings.json` (use the absolute path of your checkout):

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "/path/to/agent-sound-notifier/hooks/claude-notify.sh start 2>/dev/null || true", "async": true } ] }
    ],
    "Stop": [
      { "hooks": [ { "type": "command", "command": "/path/to/agent-sound-notifier/hooks/claude-notify.sh stop 2>/dev/null || true", "async": true } ] }
    ]
  }
}
```

Also turn off Claude Code's own tab title, otherwise it overwrites the status:

```json
{ "env": { "CLAUDE_CODE_DISABLE_TERMINAL_TITLE": "1" } }
```

Start a new Claude Code session (or open `/hooks` once) to load them. Hooks have no controlling terminal, so the script writes the title to the terminal device of the nearest ancestor process (the `claude` CLI). In the Claude desktop app there is no terminal, so only the sound plays.

## PyCharm project tabs

The local companion is required for automatic upper project-tab updates. It polls the shared status once per second, reads no conversations, and uses PyCharm's title-info extension point to refresh **all open project frames**, including inactive macOS window tabs. It enables `Settings → Tools → Terminal → Use application title as tab name → Always` so that individual agent tabs retain their OSC status dots. **Do not disable this setting:** it hides terminal-tab status as well, not just window-title text. Project totals are independently supplied by the companion. Its project-only frame-title builder omits the selected file, folder and terminal name: e.g. `learning-sandbox 🟡 2/3 finished · ⚪ 1 running`. With no live sessions only the project name appears. Individual terminal tabs keep their own ⚪/🟡 titles. This integration does not add chat recommendations or change prompts, models, or token throughput.

Build against your installed PyCharm 2026.2 SDK and its bundled JDK:

```sh
sh pycharm-plugin/build.sh
```

In PyCharm, use **Settings → Plugins → gear → Install Plugin from Disk…**, select `pycharm-plugin/build/agent-project-status.zip`, and restart the IDE when your running chats can safely be closed. Do not restart an IDE containing active agent work just to install this update. No terminal selection is needed after installation. Existing sessions enter the new cache format on their next start/stop event. With no live sessions, the companion adds no status to the project title.

This build is limited to PyCharm/IntelliJ build `262.*`, the locally compiled API version. For another installation, set `PYCHARM_HOME` to its `Contents` directory and `JAVA_HOME` to a JDK 21+ if needed; compatibility with other IDE versions must be verified before changing the plugin's build range. No Gradle or downloaded IDE SDK is required; the build uses Python 3 for ZIP packaging.

For development, run `npm install`, `npm test`, `npm run typecheck`, `sh pycharm-plugin/test.sh`, and `sh pycharm-plugin/build.sh`. The Java tests exercise the real shell writer → isolated cache → project-title reader and the IDE frame-title-builder API, without changing live IDE titles or playing sounds. Manual validation still required: keep one project selected while agents in another start, finish, and start again; both project tabs must update without clicking.
