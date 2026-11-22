# Vokabeltrainer

Karteikarten-, Schreib- und Prüfungstrainer für die Self-study-Vokabeln (155 Einträge) – Android-App für Handy und Tablet.

**Neueste Version herunterladen:** [dist/Vokabeltrainer.apk](https://raw.githubusercontent.com/Mymaxyt/voctrainer/main/dist/Vokabeltrainer.apk)

Die App prüft beim Start `version.json` in diesem Repo und meldet neue Versionen selbst.

## Aufbau
- `src/template.html` – die komplette App (HTML/CSS/JS, läuft in einer WebView)
- `src/vocab.json` – Vokabeln mit deutschen Abfragetexten, Lückensätzen und Synonym-Hinweisen
- `src/build_apk.py` – baut die APK ohne Android-SDK (DEX, Manifest, Ressourcen von Hand)
- `build.py` – App-HTML erzeugen, APK bauen, signieren, `dist/` und `version.json` aktualisieren
- `version.json` – aktuelle Version für die Update-Prüfung der App

Der Lernstand, das Fehlerprotokoll und der Sync-Token liegen nicht hier, sondern auf den Geräten bzw. verschlüsselt im privaten Gist.
Der Signierschlüssel ist absichtlich nicht im Repo.
