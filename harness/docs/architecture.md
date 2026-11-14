# Architektur, Stack und Codekonventionen

## Bausteine und Verantwortlichkeiten

- **Pi lifecycle handler:** setzt bei `agent_start` den Terminaltitel auf einen neutralen Punkt und bei `agent_settled` auf einen gelben Punkt. Das endgültige Ereignis wird statt `agent_end` verwendet, weil Zwischenläufe automatisch fortgesetzt werden können.
- **Audio adapter:** startet `/usr/bin/afplay` mit `/System/Library/Sounds/Pop.aiff` bei halber Lautstärke.
- **Lokaler Statuswriter:** `hooks/agent-status.sh` schreibt atomar pro TTY den Zustand und Prozess unter einem Hash des Git-Roots (sonst Arbeitsverzeichnis) sowie `.project` als Zuordnung. Nur das eigene Terminal erhält einen OSC-Titel mit Punkt und Agentname. Pi und Claude verwenden denselben Writer.
- **PyCharm-Companion:** `pycharm-plugin/src/agent/notifier/ProjectStatus.java` liest lokale Zustände und zählt nur lebende Prozesse. `AgentTitleProvider.java` pollt einmal pro Sekunde außerhalb des UI-Threads und meldet Änderungen auf dem UI-Thread über `TitleInfoProvider.TOPIC` an alle Projektframes. Der Timer startet auch ohne Custom-Header-Listener; native macOS-Tabs dürfen nicht von Terminalfokus abhängen. Er wird beim IDE-Shutdown entsorgt.

Die Pi-Extension bleibt ein TypeScript-Modul. Für zuverlässig aktualisierte obere Projekttabs ist zusätzlich das lokale PyCharm-Plugin nötig. Es liest ausschließlich den Cache, ohne Netzwerk oder Gesprächsinhalte. Die Einstellung „Use application title as tab name“ bleibt aktiviert (Modus „Always“), damit die OSC-Statuspunkte in einzelnen Terminaltabs sichtbar bleiben. Sie auszuschalten versteckt auch die Agent-Titel. `AgentFrameTitleBuilder.java` ersetzt den offenen IDE-Dienst `FrameTitleBuilder`: Projektname bleibt erhalten, ausgewählte Datei/Ordner/Terminal werden ausgelassen. Die Projektübersicht wird unabhängig ergänzt, beispielsweise `learning-sandbox 🟡 2/3 finished · ⚪ 1 running`. Die Titelberechnung ist rein lokal und greift nicht in Agent-Läufe ein.

## Datenfluss und Schnittstellen

```text
Pi agent_start / Claude UserPromptSubmit → Statuswriter → ⚪ Agent (eigener Terminaltab)
Pi agent_settled / Claude Stop           → Statuswriter → 🟡 Agent + macOS-Sound
                                                  │
                                            lokaler Cache
                                                  ↓ (1 s, unabhängig vom Fokus)
                                            PyCharm-Companion
                                                  ↓
                                            Projekttab: learning-sandbox 🟡 2/3 finished · ⚪ 1 running
```

Der Titelindikator gilt nur für den interaktiven TUI-Modus. Es werden keine Prompt-, Transcript- oder Modellinformationen benötigt. Fehler beim Audio oder Setzen des Titels dürfen den Agent-Lauf nicht beeinflussen.

## Entscheidungen und offene Punkte

Die Agent-Implementation liegt in `extensions/agent-sound-notifier.ts` und `hooks/`; das Companion wird separat über `pycharm-plugin/build.sh` gegen die lokal installierte IDE gebaut (aktuell nur Build 262.* freigegeben) und installiert. Live-Nachweis für inaktive Projekttabs steht noch aus. Audioausgabe: macOS über `afplay`; Windows getrennt über verstecktes PowerShell (`Media.SoundPlayer`, Fallback Systemsound), in Pi-Extension (`completionSoundCommand`) und Claude-Hook (Git-Bash-Zweig per `uname`). Unter Windows kein Statuswriter, keine Tabpunkte, kein Companion, da keine TTY-Geräte. Linux, Remote-Audio-Relay und Benutzereinstellungen sind vertagt.

## Stack und Abhängigkeiten

Die Extension ist TypeScript für die Pi Extension API. Sie wurde mit Pi 0.87.1 geladen und Node.js 26.8.1 entwickelt; `package.json` verlangt Node.js 22.19 oder neuer. Pi lädt die TypeScript-Extension aus dem lokalen Paket. Zielsystem ist macOS; ein Audio-Framework oder weitere Laufzeitabhängigkeiten werden für die Agent-Integration nicht benötigt. Das separate Companion nutzt Java 21 und die API der lokal installierten PyCharm-IDE (Build 262.*), ohne Gradle-Abhängigkeit; Python 3 paketiert das Plugin-ZIP.

## Codekonventionen

Kleiner, klar abgegrenzter Extension-Einstieg. Aufruf des Audio-Players mit festgelegtem ausführbarem Programm und Argumenten, ohne Shell-Interpolation. Den gemeinsamen Statuswriter für Pi nur im `tui`-Modus aufrufen; Audio- und UI-Fehler abfangen, damit sie den Pi-Agent-Lauf nicht stören. Abhängigkeiten nur ergänzen, falls ein konkreter Bedarf entsteht.

Das Companion liest den Cache im Hintergrund; der UI-Thread erhält nur fertige Titel und Änderungsnachrichten. Kein Terminalfokus als Trigger. Dateien atomar ersetzen, temporäre/ungültige Einträge ignorieren und Prozesslebendigkeit prüfen; IDE- und Agent-Lifecycle nicht durch Cachefehler blockieren.

## Qualitätswerkzeuge

TypeScript 5.9.3, `tsx` 4.23.15 und Node.js `node:test` werden als Entwicklungswerkzeuge verwendet. Die Befehle `npm run typecheck` und `npm test` sind eingerichtet.
