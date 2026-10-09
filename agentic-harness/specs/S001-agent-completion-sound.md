# Agent Completion Sound

- **State:** Modified
- **Ziel und Nutzer:** Eine Person, die Coding Agents (Pi, Claude Code) vorwiegend im PyCharm-Terminal nutzt, soll durch einen kurzen Ton bemerken, wenn der Coding Agent vollständig fertig ist.
- **Beschreibung:** Auf macOS wird nach Abschluss eines Agent-Laufs (Pi über die Extension, Claude Code über Hooks) genau ein kurzer lokaler Sound abgespielt und der zugehörige PyCharm-Terminal-Tab vorübergehend mit einem gelben Punkt im Titel markiert. Mehrere Agents eines Projekts teilen sich einen gemeinsamen Tab-Status.
- **Nicht im Umfang:** PyCharm-Plugin, Modell-/Provider-spezifische Integration, Desktop-Popup, Sound bei Zwischen-Turns oder Berechtigungsfragen, Netzwerkzugriff und plattformübergreifende Audioausgabe.

## Akzeptanzkriterien

- **AK1:** Ein vollständig abgeschlossener Agent-Lauf spielt genau einen kurzen Ton ab.
- **AK2:** Ein Turn-Ende mit automatischer Fortsetzung spielt noch keinen Abschluss-Ton; der Ton kommt erst nach dem endgültigen Settling.
- **AK3:** Ein Fehler beim Starten des Audio-Players beendet oder beeinträchtigt die Pi-Agent-Sitzung nicht.
- **AK4:** Das Verhalten ist unabhängig vom gewählten Modell oder Provider; die Extension liest oder verändert keine Prompt- oder Transcript-Inhalte.
- **AK5:** Im interaktiven TUI wird beim Arbeiten ein neutraler Punkt im Terminaltitel und nach dem endgültigen Settling ein gelber Punkt angezeigt.
- **AK6:** Beim Start des nächsten Agent-Laufs wechselt die Tab-Markierung vom gelben Abschluss-Punkt zurück zum neutralen Arbeitspunkt.
- **AK7:** In Claude Code spielt ein `Stop`-Hook (`hooks/claude-notify.sh stop`) nach jeder abgeschlossenen Antwort denselben Ton ab; ein Fehler des Players blockiert Claude Code nicht.
- **AK8:** Im Claude-Code-CLI setzt `UserPromptSubmit` den Terminaltitel auf den neutralen Punkt und `Stop` auf den gelben Punkt; ohne erreichbares Terminal (z. B. Desktop-App) wird nur der Ton abgespielt. Claudes eigener Titel ist dafür abgeschaltet (`CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1`).
- **AK9:** Laufen mehrere Agents (Pi, Claude Code) im selben Projekt (Git-Root, sonst Arbeitsverzeichnis), zeigen alle ihre Terminal-Tabs denselben Projektstatus mit Anzahl: solange mindestens einer arbeitet „⚪ N arbeitet“ (ggf. „· 🟡 M fertig“), sonst „🟡 M fertig“. So zeigt auch der PyCharm-Projekt-Tab mit dem ausgewählten Terminal den Gesamtstatus.
- **AK10:** Bei mehreren Agents nennt jeder Tab zusätzlich den eigenen Stand („hier 🟡 Claude“), bei einem nur den Agent („· Pi“). Beendete Agent-Prozesse zählen nicht mit; andere Projekte werden getrennt gezählt.

## Nachweise

- **AK1:** Unit-Test des registrierten Handlers bestanden; direkter macOS-`afplay`-Smoke-Test bestanden. Live-Pi-Abschluss in PyCharm noch offen.
- **AK2:** Unit-Test bestätigt, dass ausschließlich `agent_settled` registriert wird.
- **AK3:** Unit-Test mit synchron fehlschlagendem Audioadapter bestanden; asynchrone Playerfehler werden geloggt.
- **AK4:** Codeprüfung bestätigt Lifecycle-only Verhalten ohne Modell-/Transcript-Zugriff.
- **AK5/AK6:** Unit-Tests prüfen den Statuswechsel start → stop nur im TUI und dass andere Modi keinen Terminaltitel ändern; der echte PyCharm-Tab muss noch manuell geprüft werden.
- **AK7:** Hook-Skript ausgeführt (Exit 0, Ton hörbar); Hook-Einträge per `jq` validiert.
- **AK8:** Manueller Test im PyCharm-Terminal: direkt an das TTY geschriebener Titel erscheint und wird von Claude Code nicht überschrieben; Skript findet das TTY über die Prozesskette. Live-Durchlauf ⚪ → 🟡 in neuer Sitzung offen.
- **AK9/AK10:** 6 Tests von `hooks/agent-status.sh` mit simulierten Terminals bestanden (Einzel-/Mehrfachstatus, getrennte Projekte, beendete Prozesse, Tab-Wechsel, ungültige Aufrufe); Gegenprobe mit abgeschaltetem Prozessfilter schlägt fehl. Live-Aufruf schrieb den Titel an das TTY des laufenden `claude`-Prozesses (Exit 0). Sichtprüfung mit zwei gleichzeitigen Agents im PyCharm-Projekt-Tab offen.
- **Gate:** Noch offen, bis Audio und Tabtitel in einem vollständigen Pi-/PyCharm-Lauf manuell nachgewiesen sind.
