# Projektprofil – Grenzen und Befehle

> - **Typ:** Projektdoku
> - **Status:** Sound und Tabtitel-Indikator implementiert; manueller PyCharm-Smoke-Test noch offen.
> - **Zuständigkeit:** Den aktuellen Meilenstein, Projektgrenzen und ausführbare Befehle festhalten.
> - **Gilt bei:** Einordnung jeder Aufgabe über `AGENTS.md`; projektspezifisches Befüllen bei `agentic-harness/harness/init.md`.
> - **Ladebeziehungen:** Einstieg über `AGENTS.md` und `agentic-harness/harness/core.md`. Architektur bei Bedarf: `agentic-harness/docs/architecture.md`; Testpraxis: `agentic-harness/docs/testing.md`.
> - **Nicht zuständig:** Architekturdetails, Codekonventionen oder Akzeptanzkriterien wiederholen.

## Universeller Rahmen

Dieses Profil bleibt kurz und nennt nur bestätigte Grenzen und tatsächlich verfügbare Befehle. Details liegen in den zuständigen Projekt-Docs. Ein geklärtes Init ist kein bestandenes Produkt-Gate.

## Projektspezifische Befüllung

### Ziel und erster Meilenstein

`agent-sound-notifier` benachrichtigt Nutzer von Coding Agents (Pi als Extension, Claude Code über Hooks), die im PyCharm-Terminal arbeiten. Beim endgültigen Abschluss eines Agent-Laufs spielt sie einen kurzen Sound ab und markiert den Terminal-Tab im Titel gelb.

Für Claude Code liefert `hooks/claude-notify.sh` dasselbe Verhalten über Hooks in `~/.claude/settings.json`: `UserPromptSubmit` setzt den neutralen Punkt, `Stop` den gelben Punkt und den Ton. Der nächste Vorfahrenprozess mit TTY (`claude`) identifiziert Agent und Tab; Claudes eigener Titel ist per `CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1` abgeschaltet.

Beide Integrationen melden ihren Stand an `hooks/agent-status.sh`. Es führt je Projekt (Git-Root, sonst Arbeitsverzeichnis) eine Statusdatei pro Terminal und die Root-Zuordnung `.project` unter `~/.cache/agent-sound-notifier/`. Einzelne Terminals zeigen nur Punkt und Agentname. Das lokale Companion unter `pycharm-plugin/` aggregiert lebende Sessions und aktualisiert alle Projektfenstertitel einmal pro Sekunde ohne Terminalwechsel. Beispiele: `learning-sandbox 🟡 2/3 finished · ⚪ 1 running`, `learning-sandbox 🟡 3/3 finished`, `learning-sandbox ⚪ 3 running`. Der Frame-Titelbuilder lässt die ausgewählte Datei, Ordner oder den Terminalnamen weg, ohne einzelne Agent-Tabtitel zu deaktivieren.

Die TypeScript-Extension nutzt `agent_start` und `agent_settled` und ruft für den Tabtitel das gemeinsame Statusskript auf. PyCharm kann Terminaltabs über OSC-Titel umbenennen. Zielsystem ist macOS. Für automatische obere Projekttabs ist ein kleines lokales PyCharm-Plugin jetzt ausdrücklich Teil des Umfangs; die Terminaltitelanzeige bleibt aktiviert, damit die Statuspunkte nicht versteckt werden. Modellabhängige Integration, Desktop-Popups und zusätzliche Sounds bleiben außerhalb des Umfangs.

### Betrieb, Daten und Freigaben

Die Extension läuft im Pi-Prozess und nutzt dessen Lifecycle-API. Audio wird lokal auf dem Rechner abgespielt, auf dem Pi läuft. Es werden keine Gesprächsinhalte oder Nutzerdaten übertragen. Pi-Extensions laufen mit den Rechten des Pi-Prozesses; nur vertrauenswürdiger Code darf geladen werden.

### Start und Prüfstatus

Am Projektroot:

- `npm install` — Abhängigkeiten installiert.
- `npm test` — PASS: 11 Tests (4 Extension, 7 Statusskript).
- `npm run typecheck` — PASS: TypeScript-Prüfung.
- `sh pycharm-plugin/test.sh` — PASS: reale Shell→Cache→Java-Integration mit drei Sessions, getrennten Projekten, Start/Stop/Neustart und toten/ungültigen Einträgen, ohne Live-Titel oder Audio.
- `sh pycharm-plugin/build.sh` — PASS: gegen installiertes PyCharm 2026.2 / JBR 25 kompiliert; ZIP unter `pycharm-plugin/build/agent-project-status.zip` (ignoriertes Buildartefakt), Kompatibilitätsbereich 262.*.
- `sh -n hooks/agent-status.sh hooks/claude-notify.sh pycharm-plugin/build.sh pycharm-plugin/test.sh` — PASS: Shellsyntax.
- Regression am 2026-10-09 korrigiert: Companion aktiviert Terminal-Anwendungstitel im Modus `ALWAYS`, statt die einzelnen Agent-Titel zu verstecken; Projektübersicht zeigt nach präzisiertem Auftrag `🟡 2/3 finished · ⚪ 1 running` direkt hinter dem Projektnamen; ausgewählte Dateien/Terminalnamen werden durch einen eigenen Frame-Titelbuilder ausgelassen. Alle oben genannten automatischen Checks auf diesem Stand erneut bestanden, zusätzlich ein Test des realen IDE-FrameTitleBuilder-Vertrags (Projektname, leerer Dateititel, Statusformat und Plugin-Verkabelung). Einstellung in laufender IDE aktiviert; bestehende Tabs zeigten beim anschließenden visuellen Check weiterhin `Local`, daher sichtbare Wiederherstellung noch nicht abgenommen. Aktualisiertes JAR mit Backup für nächsten IDE-Start installiert; IDE nicht neu gestartet.
- Companion lokal für nächsten IDE-Start installiert: `~/Library/Application Support/JetBrains/PyCharm2026.2/plugins/agent-project-status/`; JAR-Metadaten und Implementation geprüft. Laufende IDE nicht neu gestartet; sichtbare Projektupdates noch nicht abgenommen.
- `pi install "$(pwd)"` — persönliche Pi-Installation ausgeführt; `pi list` zeigt das Paket `../../Code/python/agent-sound-notifier`.

Node.js 26.8.1, Pi 0.87.1 und macOS `/usr/bin/afplay` wurden lokal festgestellt. Direkter Soundplayer-Smoke-Test `afplay -v 0.5 /System/Library/Sounds/Pop.aiff` — PASS. Der vollständige Lifecycle-zu-Audio-und-Tabtitel-Smoke-Test in einer echten Pi-Sitzung im PyCharm-Terminal bleibt offen.

### Nächster Schritt und offene Entscheidungen

Companion in PyCharm laden (Installation siehe Root-README) und IDE erst nach Ende laufender Chats neu starten. Danach in einem anderen Projekt arbeiten und im inaktiven Projekt drei Sessions starten/abschließen/erneut starten: Die obere Übersicht muss ohne Klick wechseln; einzelne Coding-Tabs dürfen nur Punkt + Agent zeigen. Dieser Live-Nachweis sowie der vollständige Pi-Audio-Lauf bleiben offen; keine bestandene UI-Abnahme behaupten. Windows/Linux, Remote-Audio-Relay und konfigurierbare Sounds bleiben vertagt.
