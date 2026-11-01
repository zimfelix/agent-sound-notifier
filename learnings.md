# Learnings

Dieser Kopf erklärt den Ablauf und ist in allen Projekten gleich; `tools/update.py` hält ihn aktuell. Projekteinträge stehen unter der Markierung weiter unten.

## So arbeiten wir

Hierher gehören Stellen, an denen der **Harness** (Core oder ein Skill) nicht so funktioniert hat, wie er soll, und offene Fragen dazu an Felix. Normale Projektfehler gehören nicht hierher.

```text
Fehler beim Arbeiten
 ├─ Ursache im Projektcode ──────────▶ einfach fixen, kein Eintrag
 ├─ Ursache in einem Skill ──────────▶ lokal weiterarbeiten: Abweichung als Projektregel unter die Linie in AGENTS.md
 │                                     + Eintrag hier. Kleiner, eindeutiger Skill-Fehler: direkt im v6-Repo korrigieren
 └─ Ursache im Core (Arbeitsweise) ──▶ nie im Projekt ändern, nur Eintrag hier
```

| | Wo |
|---|---|
| **Bleibt lokal** | Projektregeln unter der Linie in `AGENTS.md`, `PROJECT.md`, Specs, Code |
| **Kommt hierher** | Vorschläge für Core oder Skills, Konflikte zwischen Skills, Fragen an Felix |
| **Wird übernommen** | in der Sichtung im Repo `agentic-harness-v6`, etwa wöchentlich oder ab drei offenen Einträgen: `python3 tools/learnings.py` zeigt die offenen Einträge aller Projekte. Übernommen wird nach „Reviewing and adopting learnings“ in der `AGENTS.md` des v6-Repos: einordnen, knapp formulieren, Prüfschleife (sinnvoll, keine Wiederholung, präzise, richtig eingeordnet, ufert nicht aus, prüfbar), erst dann übernehmen |

Status: `offen` → `übernommen (v6 <commit>)` · `lokal belassen` · `verworfen`. Nach der Sichtung löscht der Agent erledigte Einträge im Projekt und entfernt Projektregeln, die v6 jetzt selbst löst; die Geschichte steht im v6-Commit. In den Core kommt nur, was sich in mindestens zwei Projekten bewährt hat.

**Für den Agenten im Projekt:** Zu Beginn einer Aufgabe die offenen Einträge kurz prüfen und einen Eintrag, der die Aufgabe berührt, kurz ansprechen. Neue Einträge im Format unten, neueste oben; keine Secrets, keine Gesprächsprotokolle, keine bestätigten Regeln behaupten. **Im v6-Repo:** vor Harness-Arbeit `python3 tools/learnings.py` ausführen und neue Einträge mit Felix sichten.

## Format

```markdown
## JJJJ-MM-TT · Kurztitel · offen
- **Ziel:** core | skill:<name> | projekt
- **Für Felix:** ja/nein; wenn ja, welche Entscheidung er treffen muss
- **Beobachtet:** was passiert ist und was erwartet war
- **Lokal gelöst:** wie weitergearbeitet wurde (Projektregel, Commit) oder „nicht gelöst“
- **Vorschlag für v6:** konkrete Änderung und betroffene Datei
- **Beleg:** Datei, Commit oder Test
```

<!-- learnings:entries · Einträge unter dieser Zeile, neueste oben -->
