# Testpraxis

## Verhalten, Risiken und gewählte Tests

Unit-Tests prüfen, dass `agent_start` und `agent_settled` den neutralen beziehungsweise gelben Tabtitel setzen, nur den interaktiven TUI-Modus verändern, der Audioadapter einmal läuft und synchrone Audiofehler toleriert. Ein manueller Smoke-Test muss noch belegen, dass PyCharm den OSC-Titel tatsächlich im Terminal-Tab darstellt und der Nutzer den Indikator korrekt versteht.

## Werkzeuge, Teststruktur und Isolation

Die TypeScript-Tests liegen in `tests/agent-sound-notifier.test.ts` und `tests/agent-status.test.ts`; sie verwenden Node.js `node:test` über `tsx`. Tests injizieren einen Fake-Audioadapter, temporäre Projekte/Statusdateien und simulierte TTY-Dateien; sie spielen keinen Ton ab. `npm run typecheck` prüft Extension und Tests. `pycharm-plugin/test.sh` kompiliert und startet `pycharm-plugin/tests/ProjectStatusTest.java`, das den echten Shellwriter mit dem Java-Leser verbindet: drei Sessions, Projekttrennung, Git-Unterverzeichnisse in den Shelltests, Start/Stop/erneuter Start, tote Prozesse, partielle und ungültige Einträge. `AgentFrameTitleBuilderTest.java` prüft zusätzlich den tatsächlichen IDE-Titelbuilder-Vertrag: nur Projektname, kein ausgewählter Datei-/Terminaltitel, Statusformat und Service-Override im Plugin-Deskriptor. Der Plugin-Build prüft gegen die installierte IDE-API. Diese Nachweise belegen keine sichtbare Aktualisierung nativer macOS-Projekttabs.

## Ausführungsanlässe und offene Nachweise

Nach Änderungen am Handler oder Audioadapter laufen `npm test` und `npm run typecheck`; bei Status-/Companion-Änderungen zusätzlich Java-Integration, Plugin-Build und Shellsyntax. Vor einem Release zusätzlich ein manueller Live-Smoke-Test mit einem abgeschlossenen Pi-Agent-Lauf unter macOS und zwei offenen PyCharm-Projekten: im jeweils inaktiven Projekt Start, Abschluss und erneuten Start ohne Klick beobachten. Unit-Tests, Typprüfung und direkter macOS-`afplay`-Smoke-Test bestanden; vollständiger Live-Smoke-Test vom Pi-Lifecycle über den Ton bis zur sichtbaren PyCharm-Tabmarkierung noch offen. Befehle und aktuelle Ergebnisse stehen in `PROJECT.md`.
