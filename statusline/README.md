# Claude Code: minimale Statusline im Pi-Layout

Addon dieses Repositorys (ab Version 1.4), unabhängig von Sound und Tabpunkten nutzbar. Eingebunden über `statusLine` in global (Claude Code): `~/.claude/settings.json`:

```json
{ "statusLine": { "type": "command", "command": "/usr/bin/python3 /path/to/agent-sound-notifier/statusline/statusline.py" } }
```

Gestartet mit macOS `/usr/bin/python3`; keine Abhängigkeiten, kein Hintergrunddienst, keine zusätzlichen Modellanfragen.

Anzeige, angelehnt an den lokalen Pi-Footer (`~/.pi/agent/local/pi-tps-live-minimal`):

```text
~/PycharmProjects/agentic-harness-v6 (main)
~92.3 tok/s  41.2%/1M  Ø ~104.2 tok/s                         Opus 5.5 · high
```

Links: Rate der letzten abgeschlossenen Antwort, Kontextnutzung/-größe, Chat-Durchschnitt. Die Kontextanzeige wird ab **200.000 belegten Tokens orange** und ab **250.000 rot** (absolute Tokens = Prozent × Fenstergröße, unabhängig von 200k- oder 1M-Fenstern) als Erinnerung, die Session neu zu starten. Schwellen: `WARN_TOKENS`/`ALERT_TOKENS` in `statusline.py`. Die Farbcodes werden erst nach der Rechtsbündigkeit eingesetzt und verschieben sie nicht. Rechts: Modellname und Effort-Stufe aus Claude Codes Statusline-JSON (`model.display_name`, `effort.level`); ohne Effort-Feld nur der Name.

## Messdefinition und Grenzen

**Kein Live-Wert während des Streamings.** Claude Code übergibt der Statusline keine Stream-Tokens; das Transcript erhält Einträge erst je abgeschlossenem Antwortblock. Der linke Wert ist daher die Rate der letzten Antwort, sobald sie geschrieben ist.

Je Antwort (`message.id`): Output-Tokens geteilt durch die Zeit vom vorherigen Hauptkonversations-Eintrag (Prompt, Tool-Ergebnis) bis zum letzten geschriebenen Block derselben Antwort. Anders als Pi enthält das die Wartezeit bis zum ersten Token, daher `~`. `Ø` ist zeitgewichtet: Summe der Output-Tokens / Summe dieser Antwortdauern; Wartezeit des Nutzers und Tool-Laufzeit zählen nicht. Sidechain-Einträge werden ausgeschlossen, Antworten ohne bestimmbaren Start nicht gezählt.

Neue vollständige Transcript-Zeilen werden inkrementell gelesen. Fehlen Daten, steht `— tok/s`. Rechtsbündigkeit nutzt die Breite von `/dev/tty`, sonst `COLUMNS`, abzüglich 5 Spalten (Claude Code rückt die Zeile ein und kürzt sonst mit „…“, z. B. `Opus 5.5 · h…`); ohne beides folgt das Modell mit zwei Leerzeichen. Bei zu schmalem Terminal steht das Modell in einer eigenen Zeile. Der Branch wird direkt aus `.git/HEAD` gelesen (auch Worktrees), ohne `git`-Aufruf.

Das Skript liest das lokale Transcript nur zur Zählung und überträgt nichts. Der private Cache unter `cache/` enthält nur Message-IDs, Zeitstempel, Tokenzahlen und Dateipositionen, keine Prompts oder Antworten; Dateien mit Modus 0600. Ältere Cache-Formate werden automatisch neu aufgebaut. Cache kann bei geschlossenem Claude gelöscht werden.

## Prüfung und Rückbau

Sieben automatisierte Tests mit künstlichen Daten: Farbschwellen (19,9 %/20 %/24,9 %/25 % von 1M, 100 % von 200k) samt unveränderter Ausrichtung, Pi-Layout mit letzter Antwort und gewichtetem Durchschnitt, Rechtsbündigkeit/schmaler Fallback, unvollständige Zeilen, fehlende Daten, Dateikürzung, Pfad mit Branch und Modell ohne Effort. Aufruf: `cd statusline && /usr/bin/python3 -m unittest -v test_statusline.py`.

Probelauf mit einem echten Transcript durchgeführt; die tatsächliche Darstellung im laufenden Claude-Code-Terminal (Breite über `/dev/tty`) ist nur dort prüfbar.

Der Cache bleibt unter `~/.claude/statusline-minimal/cache/` (außerhalb des Repositorys). Zum Rückbau nur den `statusLine`-Eintrag aus `~/.claude/settings.json` entfernen. Die Statusline gehört zum Harness (Claude Code), nicht zum Terminal: Sie erscheint gleich in Warp, Terminal.app und dem PyCharm-Terminal.
