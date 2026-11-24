# CLAUDE.md – Wissensstand Vokabeltrainer

> **An jeden Claude, der hier weiterarbeitet:** Diese Datei ist das gemeinsame Gedächtnis zwischen mehreren
> Claude-Accounts von Max. Andere Sitzungen sehen deinen Chat **nicht**, nur dieses Repo.
> **Pflicht:** Trag jede Änderung, Entscheidung, neue Vorgabe von Max, jedes bekannte Problem und jede offene
> Idee hier ein (vor allem unter „Versionsverlauf“, „Vorgaben von Max“ und „Offene Punkte“), committe und pushe
> sie zusammen mit dem Code. Am Ende jeder Arbeitssitzung muss hier der aktuelle Zwischenstand stehen.
> Keine Passwörter, Tokens oder Schlüssel in diese Datei – das Repo ist öffentlich.

Zuletzt aktualisiert: 24.11.2026, Version 1.17 (versionCode 20), Commit „1.17: Notenprognose an dich angepasst“.

## Worum es geht
- Max Werner (GitHub: Mymaxyt), Student International Management (FH Würzburg), schreibt am
  **Do 26.11.2026 um 08:00** einen englischen Vokabeltest (Business English, Self-study-Vokabeln aus dem Buch).
- 155 Einträge = 151 verschiedene Wörter in 5 Kapiteln: 1 Industries and companies (29),
  2 Globalization and economic policy (16), 3 Corporate strategy and structure (30),
  7 Marketing strategy and product development (41), 8 Distribution and promotion (39).
- Die App läuft auf seinem Handy und seinem Samsung-Tablet; Stände synchronisieren über einen privaten Gist.
- Max kommuniziert auf Deutsch. App-Texte sind Deutsch, Übungssätze Englisch.

## Vorgaben von Max (unbedingt einhalten)
- **Streng bleiben:** „der Tippfehler ist mein Fehler“ – Tippfehler zählen als Fehler.
  „mach es dadurch aber nicht leichter. es geht nur um wirkliche synonyme“ – als richtig gelten nur echte Synonyme.
  „aber halte es schwer“ – keine Anfangsbuchstaben als Standardhilfe.
- Lücken: ein Strich je Buchstabe + englischer Hinweis in Klammern am Satzende (seit 1.16), weil sonst
  bei so vielen Vokabeln zu viele englische Wörter in eine Lücke passen.
- Prüfungsmodus: Abgabe **nicht** per Enter/eigener Tastatur (zu leicht verklickt), sondern zwei Taps auf den Knopf.
- Karteikarten haben einen eigenen Bereich auf der Startseite.
- „Zählt doch“ gibt es nicht mehr; stattdessen „Bewertung melden“ (landet im Fehlerprotokoll).
- **Urheberrecht:** Übungstexte aus dem Buch nicht übernehmen – nur eigene Sätze und Lückentexte.
- **Geheimnisse nie ins Repo:** Signierschlüssel (`*.jks`, in `.gitignore`) und Sync-Token.
- Max schickt ab und zu das **Fehlerprotokoll** (Export aus der App) – daraus Probleme ableiten.
- Antworten an Max kurz halten, auf Deutsch; beim Fertigstellen sagen, dass das Update über das Banner kommt
  (zum Installieren Samsung „Auto Blocker“ kurz ausschalten).

## Aufbau
- `src/template.html` – gesamte App (HTML/CSS/JS, ~1700 Zeilen), läuft in einer WebView. Platzhalter
  `/*DATA*/[]`, `/*TEXTS*/[]`, `/*ENGINE*/`, `/*VERSION_NAME*/`, `/*VERSION_CODE*/` werden von build.py gefüllt.
  Bildschirme (`<section class="screen">`): home, progress, logScreen, syncScreen, exam, resultScreen, train, cards.
  Speicher: `localStorage` über `store.get/set`; Schlüssel in `SYNC_KEYS` lösen den Sync aus.
- `src/engine.js` – reine Rechenlogik ohne Oberfläche (`module.exports = Engine`), von Node testbar.
- `src/vocab.json` – je Zeile ein Eintrag: `c` Kapitel, `n` Nummer, `e` englisch, `d` deutsch, `q` deutscher
  Abfragetext (verrät nie das Wort), `a` akzeptierte Formen/Synonyme, `s` Prüfungssatz mit `___`, `g` Lückenwort, `y` verwandte Wörter, die **nicht** als richtig zählen (nur Hinweis „Synonym, aber nicht gefragt“).
- `src/training.py` – `T`: je Eintrag zwei eigene Übungs-Lückensätze (Prüfungssätze `s` kommen absichtlich nicht vor);
  `H`: 155 englische Hinweise (≤ 45 Zeichen, verraten das Wort nicht); `TEXTS`: 17 eigene Lückentexte nur für die
  Prüfungssimulation (`[[i]]` = Lücke für Eintrag i; Text „3.4“ deckt 3.4 und 3.5 ab).
- `src/prompts.py`, `src/sentences.py` – alte Quellen von `q`/`s`, werden von build.py nicht mehr gelesen.
- `src/build_apk.py` + `src/dexasm.py` – baut die APK **ohne Android-SDK** (DEX-Assembler, binäres Manifest,
  resources.arsc, Icon von Hand). Paket `de.maxwerner.vokabeln`, MainActivity = WebView, minSdk 26, targetSdk 29.
  Native Teil: Link `vokabeltrainer://update?url=…` → App lädt die APK selbst (DownloadManager) und öffnet die Installation.
- `build.py` – HTML erzeugen, APK bauen, mit jarsigner signieren, `dist/Vokabeltrainer.apk` + `version.json` schreiben.
- `tests/engine.test.js` (17 Testgruppen), `tests/fsrs_cases.json` (+ `make_fsrs_cases.py`, Abgleich mit py-fsrs).
- `tools/check_content.py` – prüft Sätze, Hinweise, Lückentexte (muss 0 Fehler melden).
- `tools/dexcheck.py` – prüft die DEX-Datei in der fertigen APK.

## Bauen, prüfen, veröffentlichen
```bash
TZ=Europe/Berlin node tests/engine.test.js          # "engine: 17 Testgruppen bestanden"
python3 -I tools/check_content.py                   # "310 Übungssätze, 17 Lückentexte mit 155 Lücken", 0 Fehler
python3 -I build.py --html /pfad/index.html 1.18 21 # nur App-Seite zum Testen im Browser (Playwright ist gut dafür)
KEYSTORE=/pfad/key.jks KEYPASS=<von Max> python3 -I build.py 1.18 21 "Kurze Notiz für das Update-Banner"
jarsigner -verify dist/Vokabeltrainer.apk && python3 -I tools/dexcheck.py dist/Vokabeltrainer.apk
git -c user.name=Mymaxyt -c user.email=Mymaxyt@users.noreply.github.com commit -am "1.18: …"
git push
```
- Signierschlüssel: `key.jks`, Alias `max`. Max gibt Datei und Passwort direkt im Chat (nie committen).
  **Ohne genau diesen Schlüssel lässt sich kein Update über die installierte App spielen.**
- versionCode immer um 1 erhöhen (aktuell 20 → nächste 21). Die App vergleicht ihn mit `version.json`
  (`https://raw.githubusercontent.com/Mymaxyt/voctrainer/main/version.json`) und zeigt dann das Update-Banner.
- Nach dem Push prüfen, dass raw.githubusercontent.com die neue `version.json` und eine identische APK ausliefert.
- UI-Tests (Playwright) liegen nicht im Repo; bisher: Lernfluss, Sync zwischen zwei Geräten, Tastatur,
  Prüfungsabgabe mit zwei Taps, Lücken-Darstellung, Prognose-Panel (Handy 412 px hell, Tablet 1280 px dunkel).
  Bei UI-Änderungen Screenshots machen und ansehen.

## Lernmodell (engine.js)
- **Verlauf je Wort** (Schlüssel `norm(e)`, gleich geschriebene Einträge teilen sich einen Verlauf):
  `hist[key] = [[zeit, note, modus, fehlerart?, partner?], …]`
  - note: 1 falsch · 2 richtig mit Hilfe · 3 ohne Hilfe richtig getippt
  - modus: w Schreiben (Dt→En) · c Lückensatz · t Lückentext · x Prüfungssatz · k Karteikarte · l vor 1.15 übernommen
  - fehlerart: s Rechtschreibung · f Form · v Verwechslung (mit partner) · w falsches Wort · n nicht gewusst
- **Lerntag** 04:00–04:00. **Tagesziel:** jedes Wort einmal ohne Hilfe richtig. Nach Fehler: Fehlerart + Buchstabenvergleich,
  Lösung abtippen, Wort kommt nach ~1 und ~10 Minuten wieder (successive relearning).
- **Lernstufen** 0 Neu · 1 In Arbeit · 2 Gefestigt (2× richtig, ≥ 10 Min. Abstand) · 3 Sicher (an 2 Tagen, 1× im Satz) ·
  4 Prüfungsfest (3× an 3 Tagen, 2× im Satz). Fehler/Tipp setzen zurück, Karteikarten zählen nicht.
- **FSRS-6** mit offiziellen Standardparametern (gegen py-fsrs geprüft): `retr(S, t) = (1 + FACTOR·t/S)^DECAY`.
- `pick()` wählt die nächste Frage (Abstand: nicht unter den letzten 3 und < 2 Min. her), `modeFor` den Modus.
- Migration: alte 1.14-Stände über `absorbLegacy` als Modus `l`; `tidy()` fasst Duplikate (< 2 s) zusammen;
  Antworten, die heute erlaubt wären, werden nicht als Fehler übernommen.

## Notenprognose (seit 1.17, Fortschritt → Notenprognose)
- **Persönlicher Faktor k** auf die FSRS-Stabilität: aus „Abrufen über Nacht“ (`recalls`: erste getippte Antwort
  eines Lerntags zu einem Wort, das an einem früheren Tag schon dran war; Hilfe = falsch; Modus `l` zählt nicht als Ziel).
  `calibrate`: MAP mit Prior log k ~ N(0, 0,7²), Goldener Schnitt auf [−3, 3], Unsicherheit aus der Krümmung.
- **Szenarien:** „Stand jetzt“ und „Mit Lernplan bis zur Prüfung“ (`sessionsUntil`: täglich 18:00 bis 2 h vor
  Prüfung; `examRecall`: Erfolg mit p, sonst Again + Good + Good).
- **Monte Carlo** (`forecast`): 7 Stützstellen über die Unsicherheit von k, ~4200 simulierte Prüfungen mit
  n Lücken → Notenverteilung, Bereich p10–p90, Chance auf 1,0. Seed fest (mulberry 20261126).
- **Selbstkontrolle:** Abrufe über Nacht richtig vs. erwartet (Standard- und angepasstes Modell); `examCheck`
  vergleicht Prüfungssimulationen (Modi x/t) mit dem Modell.
- **Annahmen einstellbar:** Lückenzahl `settings.n` (Standard 30), Notenschlüssel `key1` (1,0 ab, Standard 95 %)
  und `key4` (4,0 ab, Standard 50 %), dazwischen linear (`gradeKey`, `gradeOf`).
- Recherche dahinter: DASH (Lindsey et al. 2014), HLR (Settles & Meeder 2016), FSRS-Benchmark (Expertium;
  angepasste Parameter bei ~84 % besser, wenig Daten → zum Durchschnitt schrumpfen; Same-Day-Reviews zählen nicht),
  Kaur et al. 2025 (Übung↔Prüfung ρ 0,60–0,72 → Bereich statt Punktwert), Pan & Rickard 2018 (anderes Format
  → schwächerer Transfer), Notenschlüssel schwanken (DHBW 1,0 ab 98 %, IHK 1 ab 92 Punkten, 4 ab 50 %).
- Grenze: App-Format (Striche + Hinweis) hilft mehr als eine leere Lücke → Prognose eher zu hoch, falls die Prüfung weniger Hilfe gibt.

## Sync
- Privater GitHub-Gist (`vokabeltrainer.json`), Inhalt AES-GCM-verschlüsselt. `sync = {gist, key, token, …}` im localStorage.
- Payload v2: `{v:2, hist, settings, exams, log, logCleared, srs}`; Zusammenführen über `mergeHist`.
- Sparsam: `SYNC_GAP` 120 s, ETag-Cache, Backoff bei GitHub-Limits. Token braucht Berechtigung „gist“.

## Versionsverlauf
- 1.11 Update-Prüfung über version.json · 1.12 genauere Abfragen nach Fehlerprotokoll · 1.13 Sync sparsam/robust
- 1.14 Update installiert sich nach Download selbst
- 1.15 Neubau nach Lernforschung: Lernplan, 310 Lückensätze, 17 Lückentexte, Fehlerarten mit Buchstabenvergleich,
  Abtippen nach Fehler, „Bewertung melden“, Fortschritt mit Prognose; alte Fehler, die heute erlaubt sind, nicht übernehmen
- 1.15.1 Reiter oben übersichtlicher, Karteikarten als eigener Bereich
- 1.15.2 Prüfung nicht mehr per Enter abgeben
- 1.16 Lücken mit Strich je Buchstabe und englischem Hinweis; Synonyme überarbeitet
- 1.17 Notenprognose an Max angepasst (siehe oben)

## Offene Punkte / Ideen
- Prognose mit echten Daten von Max beobachten: Wie viele Abrufe über Nacht gibt es, wie weit weicht k von 1 ab?
- Echtes Prüfungsformat (Lückenzahl, Notenschlüssel, gibt es Hinweise?) ist unbekannt – Max fragen, falls er es weiß,
  und in den Annahmen eintragen lassen.
- Nach der Prüfung (26.11.) ggf. echte Note mit Prognose vergleichen und hier notieren.
