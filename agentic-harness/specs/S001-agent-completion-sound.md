# Agent Completion Sound

- **State:** Modified
- **Ziel und Nutzer:** Eine Person, die Coding Agents (Pi, Claude Code) vorwiegend im PyCharm-Terminal nutzt, soll durch einen kurzen Ton bemerken, wenn der Coding Agent vollständig fertig ist.
- **Beschreibung:** Auf macOS wird nach Abschluss eines Agent-Laufs (Pi über die Extension, Claude Code über Hooks) genau ein kurzer lokaler Sound abgespielt und der zugehörige PyCharm-Terminal-Tab vorübergehend mit einem gelben Punkt im Titel markiert. Einzelne Terminaltabs zeigen nur Statuspunkt und Agentname. Eine kleine lokale PyCharm-Integration zeigt den aggregierten Projektstatus unabhängig vom ausgewählten Terminal.
- **Nicht im Umfang:** Modell-/Provider-spezifische Integration, Desktop-Popup, Sound bei Zwischen-Turns oder Berechtigungsfragen, Netzwerkzugriff, Chat-Recommendations, Eingriffe in Prompts oder Token-Durchsatz und plattformübergreifende Audioausgabe.

## Akzeptanzkriterien

- **AK1:** Ein vollständig abgeschlossener Agent-Lauf spielt genau einen kurzen Ton ab.
- **AK2:** Ein Turn-Ende mit automatischer Fortsetzung spielt noch keinen Abschluss-Ton; der Ton kommt erst nach dem endgültigen Settling.
- **AK3:** Ein Fehler beim Starten des Audio-Players beendet oder beeinträchtigt die Pi-Agent-Sitzung nicht.
- **AK4:** Das Verhalten ist unabhängig vom gewählten Modell oder Provider; die Extension liest oder verändert keine Prompt- oder Transcript-Inhalte.
- **AK5:** Im interaktiven TUI wird beim Arbeiten ein neutraler Punkt im Terminaltitel und nach dem endgültigen Settling ein gelber Punkt angezeigt.
- **AK6:** Beim Start des nächsten Agent-Laufs wechselt die Tab-Markierung vom gelben Abschluss-Punkt zurück zum neutralen Arbeitspunkt.
- **AK7:** In Claude Code spielt ein `Stop`-Hook (`hooks/claude-notify.sh stop`) nach jeder abgeschlossenen Antwort denselben Ton ab; ein Fehler des Players blockiert Claude Code nicht.
- **AK8:** Im Claude-Code-CLI setzt `UserPromptSubmit` den Terminaltitel auf den neutralen Punkt und `Stop` auf den gelben Punkt; ohne erreichbares Terminal (z. B. Desktop-App) wird nur der Ton abgespielt. Claudes eigener Titel ist dafür abgeschaltet (`CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1`).
- **AK9:** Der obere PyCharm-Projekttab zeigt ausschließlich den Projektnamen und direkt danach die kompakte Projektübersicht: beispielsweise „learning-sandbox 🟡 2/3 finished · ⚪ 1 running“, „learning-sandbox 🟡 3/3 finished“ oder „learning-sandbox ⚪ 3 running“. Gelb markiert abgeschlossene Antworten, Weiß weiterhin arbeitende Agenten; ein Projekt ist erst vollständig fertig, wenn kein weißer Running-Status mehr erscheint. Ausgewählte Dateien, Ordner und Terminalnamen (z. B. „Local“) werden nicht ergänzt. Ohne lebende Sessions steht nur der Projektname. Der Status aktualisiert sich innerhalb von zwei Sekunden bei Start und Abschluss, auch für nicht ausgewählte Projekte, ohne Klick oder Terminalwechsel. Die PyCharm-Integration liest nur lokale Statusdateien; Terminaltitel dürfen die Projektübersicht nicht ersetzen. Die Einstellung „Use application title as tab name“ bleibt aktiviert, damit auch die einzelnen Agent-Tabs ihre Statuspunkte anzeigen.
- **AK10:** Jeder Coding-Terminaltab zeigt ausschließlich „⚪ Pi“, „🟡 Pi“, „⚪ Claude“ oder „🟡 Claude“, ohne Projektzahlen oder „hier“. Beendete Prozesse zählen nicht mit; Projekte (Git-Root, sonst Arbeitsverzeichnis) bleiben getrennt. Eine neue Sitzung auf demselben TTY ersetzt die vorherige.

## Nachweise

- **AK1:** Unit-Test des registrierten Handlers bestanden; direkter macOS-`afplay`-Smoke-Test bestanden. Live-Pi-Abschluss in PyCharm noch offen.
- **AK2:** Unit-Test bestätigt, dass ausschließlich `agent_settled` registriert wird.
- **AK3:** Unit-Test mit synchron fehlschlagendem Audioadapter bestanden; asynchrone Playerfehler werden geloggt.
- **AK4:** Codeprüfung bestätigt Lifecycle-only Verhalten ohne Modell-/Transcript-Zugriff.
- **AK5/AK6:** Unit-Tests prüfen den Statuswechsel start → stop nur im TUI und dass andere Modi keinen Terminaltitel ändern; der echte PyCharm-Tab muss noch manuell geprüft werden.
- **AK7:** Hook-Skript ausgeführt (Exit 0, Ton hörbar); Hook-Einträge per `jq` validiert.
- **AK8:** Manueller Test im PyCharm-Terminal: direkt an das TTY geschriebener Titel erscheint und wird von Claude Code nicht überschrieben; Skript findet das TTY über die Prozesskette. Live-Durchlauf ⚪ → 🟡 in neuer Sitzung offen.
- **AK9/AK10:** 7 Shell-Regressionstests (inklusive erneutem Start, eigenem Terminaltitel, Git-Unterverzeichnissen, Prozessfilter und ungültigen Aufrufen) bestanden. Java-Integration mit echtem Shellwriter und temporären Cache-/TTY-Dateien bestanden: drei Sessions, `🟡 2/3 finished · ⚪ 1 running`, Abschluss, erneuter Start, Projekttrennung und tote/partielle Einträge. Companion gegen installiertes PyCharm 2026.2 (262.*) kompiliert und für den nächsten IDE-Start installiert; kein Neustart aktiver Chats. Bisheriger OSC-Ansatz ist laut Betreiber-Screenshots für nicht aktive Projekttabs unzureichend. Live-Nachweis mit mehreren Projekten (Start und Abschluss ohne Klick) nach Installation der PyCharm-Integration erforderlich.
- **Regression 2026-10-09:** Lokal hinzugefügtes Companion hatte die globale Terminaltitelanzeige deaktiviert; Korrektur aktiviert sie im Modus `ALWAYS` und zeigt nach präzisiertem Auftrag `Projektname 🟡 2/3 finished · ⚪ 1 running`. Ein eigener Frame-Titelbuilder unterdrückt den ausgewählten Datei-/Terminalnamen. 11 TypeScript-/Shelltests, Typprüfung, Java-Integration, IDE-FrameTitleBuilder-Vertragstest, Plugin-Build und Shellsyntax erneut bestanden. Einstellung in der laufenden IDE aktiviert und neues JAR für nächsten Neustart installiert (Backup vorhanden). Bestehende Tabs zeigten anschließend noch `Local`; Live-Abnahme nach sicherem IDE-Neustart bleibt erforderlich. Kein Eingriff in Chat-Recommendations.
- **Gate:** Noch offen, bis Audio und Tabtitel in einem vollständigen Pi-/PyCharm-Lauf manuell nachgewiesen sind.
