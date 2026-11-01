# Project

Keep only confirmed decisions and useful continuation context. Fill from the request and repository; do not ask again for supplied/delegated decisions. Small projects need a few concrete paragraphs, not a completed questionnaire.

## Goal and boundaries

`agent-sound-notifier` benachrichtigt Nutzer von Coding Agents (Pi als Extension, Claude Code über Hooks), die im PyCharm-Terminal arbeiten: Beim endgültigen Abschluss eines Agent-Laufs spielt ein kurzer Ton, und der Terminal-Tab bekommt einen gelben Punkt im Titel. Ein lokales PyCharm-Companion zeigt den Projektstatus im Fenstertitel, z. B. `learning-sandbox 🟡 2/3 finished · ⚪ 1 running`. Dazu gehören ein Statusline-Addon (Spec S002) und ein Installer (Spec S003).

Zielsystem macOS. Windows: nur Abschlusston (PowerShell-Zweig), keine Tabpunkte, kein Companion. Außerhalb des Umfangs: modellabhängige Integration, Desktop-Popups, zusätzliche oder konfigurierbare Sounds, Linux, Remote-Audio-Relay.

Daten und Rechte: Audio und Status bleiben lokal; keine Gesprächsinhalte oder Nutzerdaten werden übertragen. Pi-Extensions laufen mit den Rechten des Pi-Prozesses; nur vertrauenswürdigen Code laden.

## Architecture and tools

Bausteine, Datenfluss, Stack und Codekonventionen: `docs/architecture.md`. Teststrategie: `docs/testing.md`.

Befehle am Projektroot:

- `npm install`, `npm test`, `npm run typecheck`
- `sh pycharm-plugin/test.sh` (Shell→Cache→Java-Integration), `sh pycharm-plugin/build.sh` (Build gegen installiertes PyCharm 262.*, ZIP unter `pycharm-plugin/build/`)
- `sh -n hooks/agent-status.sh hooks/claude-notify.sh pycharm-plugin/build.sh pycharm-plugin/test.sh`
- `cd statusline && /usr/bin/python3 -m unittest -v test_statusline.py`
- `/usr/bin/python3 -m unittest -v tests/test_install.py`
- Persönliche Installation: `pi install "$(pwd)"`; Companion unter `~/Library/Application Support/JetBrains/PyCharm2026.2/plugins/agent-project-status/`

Versionierung: Releases heißen `v<Major>.<Minor>` (Tag `v1.4`, README und Plugin `1.4`); nur `package.json` führt SemVer `1.4.0`. Der frühere Tag `v1.2.3` heißt seit 2026-10-17 `v1.2.1`; der Commit-Betreff `chore(release): 1.2.3` bleibt als veröffentlichte Historie.

Relevant skills: keine; kein Website- oder Business-Software-Projekt.

## Acceptance and current work

Letzter geprüfter Stand (2026-10-27, Installer S003): `npm test` 13 PASS, Typprüfung PASS, Statusline 7 PASS, Installer 6 PASS, Java-Integration und Plugin-Build PASS; `install.py --all` gegen eine Kopie der echten `settings.json` geprüft.

Offene Nachweise, nur durch den Betreiber prüfbar:

- Live-Abnahme Companion: IDE nach Ende laufender Chats neu starten, im inaktiven Projekt drei Sessions starten/abschließen/erneut starten. Die obere Übersicht muss ohne Klick wechseln; einzelne Coding-Tabs zeigen nur Punkt + Agent.
- Vollständiger Pi-Lauf vom Lifecycle bis Ton und sichtbarer Tabmarkierung im PyCharm-Terminal.
- Echter Windows-Lauf (Ton über PowerShell); Ton und Tabpunkt in Warp.

Nächste autorisierte Aktion: keine offene Produktaufgabe; bei der nächsten Sitzung die Live-Abnahmen mit dem Betreiber durchgehen.
