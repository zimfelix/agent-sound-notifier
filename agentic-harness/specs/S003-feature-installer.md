# Installer für drei Claude-Code-Features

- **State:** Modified
- **Ziel und Nutzer:** Eine andere Person (macOS oder Windows) soll Sound, Statusline und Output Style „Strukturiert“ ohne Handarbeit an `settings.json` übernehmen können, idealerweise indem sie ihrem Coding Agent die README-Anweisung gibt.
- **Beschreibung:** Die README gliedert das Repo in drei Features (Sound, Statusline, Output Style) und enthält eine Agent-Anleitung. `install.py` installiert oder entfernt die gewählten Features (Flags oder interaktive Abfrage), sichert vorher `settings.json`, ändert nur eigene Einträge und ist wiederholbar. Windows erhält Ton-Hooks über `bash`, macOS zusätzlich Tabpunkt-Hooks; die Statusline richtet sich unter Windows über `CONOUT$` rechtsbündig aus.
- **Nicht im Umfang:** Pi-Installation (weiter `pi install`), PyCharm-Companion, Tabpunkte unter Windows, Linux-Ton, Sitegeist/Skills/Plugins, Umbenennung des Repos.

## Akzeptanzkriterien

- **AK1:** `--all` auf macOS setzt vier eigene Hooks, `CLAUDE_CODE_DISABLE_TERMINAL_TITLE`, Statusline und Output Style; fremde Einstellungen bleiben, ein zweiter Lauf dupliziert nichts, ein Backup entsteht.
- **AK2:** `--sound` auf Windows setzt nur `Stop`/`PreToolUse` mit `bash "<Pfad mit />"` und keinen Titel-Schalter.
- **AK3:** `--uninstall` stellt die eigenen Einstellungen wieder her; eine vom Nutzer bearbeitete Style-Datei wird bei Installation gesichert und beim Entfernen nicht gelöscht.
- **AK4:** Ungültiges JSON wird nie überschrieben; ohne Terminal und ohne Flags bricht der Installer ab.
- **AK5:** Statusline-Verhalten bleibt unverändert (S002).
- **AK6:** Echter Lauf auf Windows (Ton, Statusline-Ausrichtung, Style).

## Nachweise

- **AK1–AK4:** `python3 -m unittest -v tests/test_install.py` — 6 Tests PASS (2026-10-27); Abbruch ohne Terminal manuell geprüft.
- **AK5:** `cd statusline && /usr/bin/python3 -m unittest test_statusline.py` — 7 Tests PASS (2026-10-27).
- **AK6:** offen, Abnahme durch Windows-Nutzer.
- **Gate:** AK6 offen → `Modified`.
