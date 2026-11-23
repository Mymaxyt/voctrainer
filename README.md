# Vokabeltrainer

Lernplan-, Lückensatz-, Schreib-, Karteikarten- und Prüfungstrainer für die Self-study-Vokabeln (155 Einträge, 151 verschiedene Wörter) – Android-App für Handy und Tablet.

**Neueste Version herunterladen:** [dist/Vokabeltrainer.apk](https://raw.githubusercontent.com/Mymaxyt/voctrainer/main/dist/Vokabeltrainer.apk)

Die App prüft beim Start `version.json` in diesem Repo und meldet neue Versionen selbst.

## Wie gelernt wird (ab 1.15)
- **Lernplan:** jedes Wort jeden Tag einmal ohne Hilfe richtig abrufen, meist als englischer Lückensatz (wie in der Prüfung). Nach einem Fehler: Fehlerart und Buchstabenvergleich, Lösung einmal abtippen, das Wort kommt nach etwa 1 und 10 Minuten wieder (*successive relearning*).
- **Lernstufen** sind Fakten aus dem Verlauf: Gefestigt (2× richtig, ≥ 10 Min. Abstand), Sicher (an 2 Tagen, 1× im Satz), Prüfungsfest (3× an 3 Tagen, 2× im Satz). Fehler oder Tipp setzen zurück, Karteikarten zählen nicht.
- **Prognose** für den Prüfungstermin mit dem Gedächtnismodell FSRS-6 (offizielle Standardparameter, gegen py-fsrs geprüft).
- **Prüfungssimulation** mit eigenen Sätzen und 17 Lückentexten, die im Training nie vorkommen.

## Aufbau
- `src/template.html` – die App-Oberfläche (HTML/CSS/JS, läuft in einer WebView)
- `src/engine.js` – Lernmodell ohne Oberfläche: Verlauf, Lernstufen, Tagesziel, FSRS-6, Fehlerarten, Übernahme alter Stände, Sync-Zusammenführung
- `src/vocab.json` – Vokabeln mit deutschen Abfragetexten, Prüfungssätzen und Synonym-Hinweisen
- `src/training.py` – je Vokabel zwei Übungs-Lückensätze und ein Lückentext je Buchaufgabe (eigene Texte)
- `src/build_apk.py` – baut die APK ohne Android-SDK (DEX, Manifest, Ressourcen von Hand)
- `build.py` – App-HTML erzeugen, APK bauen, signieren, `dist/` und `version.json` aktualisieren
- `tests/engine.test.js` – Tests des Lernmodells (`TZ=Europe/Berlin node tests/engine.test.js`)
- `tools/check_content.py` – prüft Übungssätze und Lückentexte (Lücken, Abdeckung, verratene Lösungswörter)
- `version.json` – aktuelle Version für die Update-Prüfung der App

Der Lernstand, das Fehlerprotokoll und der Sync-Token liegen nicht hier, sondern auf den Geräten bzw. verschlüsselt im privaten Gist.
Der Signierschlüssel ist absichtlich nicht im Repo.
