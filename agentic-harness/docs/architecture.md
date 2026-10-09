# Architektur – Bausteine und Datenfluss

> - **Typ:** Projektdoku
> - **Status:** Sound und Tabtitel-Indikator implementiert; Unit-Tests bestanden; echter PyCharm-Tab-Smoke-Test noch offen.
> - **Zuständigkeit:** Entschiedene Bausteine, ihre Aufgaben und Abhängigkeiten für den aktuellen Meilenstein erklären.
> - **Gilt bei:** Project Init sowie Architektur-, Schnittstellen- oder Strukturfragen.
> - **Ladebeziehungen:** Vorher `agentic-harness/harness/project.md` für Ziel und Grenzen lesen. Bei Codekonventionen zusätzlich `agentic-harness/docs/code.md`; bei Teststruktur `agentic-harness/docs/testing.md`.
> - **Nicht zuständig:** Agentenablauf, Code-Stil oder beauftragtes Nutzerverhalten festlegen.

## Universeller Rahmen

Ist, entschiedenes Ziel und offene Möglichkeiten nicht verwechseln. Bausteine nur für einen geklärten Bedarf vorsehen; Paket- und Technologieentscheidungen dieses Projekts hier begründen.

## Projektspezifische Befüllung

### Bausteine und Verantwortlichkeiten

- **Pi lifecycle handler:** setzt bei `agent_start` den Terminaltitel auf einen neutralen Punkt und bei `agent_settled` auf einen gelben Punkt. Das endgültige Ereignis wird statt `agent_end` verwendet, weil Zwischenläufe automatisch fortgesetzt werden können.
- **Audio adapter:** startet `/usr/bin/afplay` mit `/System/Library/Sounds/Pop.aiff` bei halber Lautstärke.
- **Lokaler Statuswriter:** `hooks/agent-status.sh` schreibt atomar pro TTY den Zustand und Prozess unter einem Hash des Git-Roots (sonst Arbeitsverzeichnis) sowie `.project` als Zuordnung. Nur das eigene Terminal erhält einen OSC-Titel mit Punkt und Agentname. Pi und Claude verwenden denselben Writer.
- **PyCharm-Companion:** `pycharm-plugin/src/agent/notifier/ProjectStatus.java` liest lokale Zustände und zählt nur lebende Prozesse. `AgentTitleProvider.java` pollt einmal pro Sekunde außerhalb des UI-Threads und meldet Änderungen auf dem UI-Thread über `TitleInfoProvider.TOPIC` an alle Projektframes. Der Timer startet auch ohne Custom-Header-Listener; native macOS-Tabs dürfen nicht von Terminalfokus abhängen. Er wird beim IDE-Shutdown entsorgt.

Die Pi-Extension bleibt ein TypeScript-Modul. Für zuverlässig aktualisierte obere Projekttabs ist zusätzlich das lokale PyCharm-Plugin nötig. Es liest ausschließlich den Cache, ohne Netzwerk oder Gesprächsinhalte. Die Einstellung „Use application title as tab name“ bleibt aktiviert (Modus „Always“), damit die OSC-Statuspunkte in einzelnen Terminaltabs sichtbar bleiben. Sie auszuschalten versteckt auch die Agent-Titel. `AgentFrameTitleBuilder.java` ersetzt den offenen IDE-Dienst `FrameTitleBuilder`: Projektname bleibt erhalten, ausgewählte Datei/Ordner/Terminal werden ausgelassen. Die Projektübersicht wird unabhängig ergänzt, beispielsweise `learning-sandbox 2/3 finished · 1 running`. Die Titelberechnung ist rein lokal und greift nicht in Agent-Läufe ein.

### Datenfluss und Schnittstellen

```text
Pi agent_start / Claude UserPromptSubmit → Statuswriter → ⚪ Agent (eigener Terminaltab)
Pi agent_settled / Claude Stop           → Statuswriter → 🟡 Agent + macOS-Sound
                                                  │
                                            lokaler Cache
                                                  ↓ (1 s, unabhängig vom Fokus)
                                            PyCharm-Companion
                                                  ↓
                                            Projekttab: learning-sandbox 2/3 finished · 1 running
```

Der Titelindikator gilt nur für den interaktiven TUI-Modus. Es werden keine Prompt-, Transcript- oder Modellinformationen benötigt. Fehler beim Audio oder Setzen des Titels dürfen den Agent-Lauf nicht beeinflussen.

### Entscheidungen und offene Punkte

Die Agent-Implementation liegt in `extensions/agent-sound-notifier.ts` und `hooks/`; das Companion wird separat über `pycharm-plugin/build.sh` gegen die lokal installierte IDE gebaut (aktuell nur Build 262.* freigegeben) und installiert. Live-Nachweis für inaktive Projekttabs steht noch aus. Audioausgabe ist auf macOS begrenzt. Windows/Linux, Remote-Audio-Relay und Benutzereinstellungen sind vertagt.
