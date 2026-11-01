# Claude-Code-Statusline mit Kontextwarnung

- **State:** Modified
- **Ziel und Nutzer:** Eine Person, die Claude Code im Terminal (PyCharm, Terminal.app, Warp) nutzt, soll Durchsatz und Kontextnutzung auf einen Blick sehen und rechtzeitig erinnert werden, eine zu volle Session neu zu starten.
- **Beschreibung:** Die Statusline zeigt Pfad (mit Branch), tok/s der letzten Antwort, Kontextnutzung/-größe, gewichteten Chat-Durchschnitt sowie Modell · Effort. Ab 200.000 belegten Kontext-Tokens erscheint die Kontextangabe orange, ab 250.000 rot.
- **Nicht im Umfang:** Pi-Footer (`~/.pi/agent/local/pi-tps-live-minimal`, separates lokales Paket), Live-Streaming-Rate, automatisches Neustarten oder Kompaktieren.

## Akzeptanzkriterien

- **AK1:** Unter 200.000 belegten Tokens ist die Kontextangabe ungefärbt.
- **AK2:** Ab 200.000 belegten Tokens ist sie orange, ab 250.000 rot; maßgeblich sind absolute Tokens (Prozent × Fenstergröße).
- **AK3:** Die Farbcodes verschieben die Rechtsbündigkeit von Modell · Effort nicht.
- **AK4:** Bestehendes Verhalten (Layout, Durchschnitt, Teilzeilen, fehlende Daten, Kürzung, Branch) bleibt unverändert.

## Nachweise

- **AK1–AK3:** `test_context_turns_orange_and_red_at_absolute_token_counts` — PASS (2026-10-21).
- **AK4:** Sechs bestehende Tests — PASS (2026-10-21).
- **Gate:** `cd statusline && /usr/bin/python3 -m unittest -v test_statusline.py` — 7 Tests PASS. Sichtprüfung der Farbe im laufenden Terminal durch den Betreiber offen.
