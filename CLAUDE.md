# CLAUDE.md – Wissensstand Vokabeltrainer

> **An jeden Claude, der hier weiterarbeitet:** Diese Datei ist das gemeinsame Gedächtnis zwischen mehreren
> Claude-Accounts von Max. Andere Sitzungen sehen deinen Chat **nicht**, nur dieses Repo.
> **Pflicht:** Trag jede Änderung, Entscheidung, neue Vorgabe von Max, jedes bekannte Problem und jede offene
> Idee hier ein (vor allem unter „Versionsverlauf“, „Vorgaben von Max“ und „Offene Punkte“), committe und pushe
> sie zusammen mit dem Code. Am Ende jeder Arbeitssitzung muss hier der aktuelle Zwischenstand stehen.
> Keine Passwörter, Tokens oder Schlüssel in diese Datei – das Repo ist öffentlich.

Zuletzt aktualisiert: 24.11.2026, Version 1.19.1 (versionCode 24): Prüfung im Format des Moodle-Übungstests, englische Definitionen, 100 Wörter aus den Kursunterlagen.

## Worum es geht
- Max Werner (GitHub: Mymaxyt), Student International Management (FH Würzburg), schreibt am
  **Do 26.11.2026 um 08:00** einen englischen Vokabeltest (Business English, Self-study-Vokabeln aus dem Buch).
- **Prüfungsstoff laut Dozent („Vocabulary revision for the test – WS 26-27“, es gibt keine offizielle Wortliste):**
  Kursmaterial „Industries and companies – vocabulary exercise“ und „Organisational structures – listening exercise
  (vocabulary)“; Self-study 1.1, 1.5, 1.6, 3.1, 3.4, 3.5, 3.6, 7.1–7.5, 8.1, 8.2, 8.3, 8.8, 2.1, 2.4.
  Dazu hat Max geschickt: Marketing overview, Industries in class 2, ein Wiederholungsblatt (Kreuzworträtsel, Kollokationen,
  Lückentext, Buchstabensalat, Fehler finden). Die Hörübung „Organisational structures“ lag NICHT vor – ihre Wörter sind
  aus Übungstest und Wiederholungsblatt erschlossen (hierarchy, span of control, chain of command, flat/tall structure …).
  Die Lesetexte der Buchkapitel stehen nicht auf der Liste.
- 255 Einträge = 251 verschiedene Wörter: 155 Self-study-Einträge (Kapitel 1, 2, 3, 7, 8) + 100 aus den Kursunterlagen
  (Kapitel-Codes W = Übungstest + Wiederholungsblatt, K1 = Kurs Industries, K3 = Kurs Organisation, K7 = Kurs Marketing).
- Die App läuft auf seinem Handy und seinem Samsung-Tablet; Stände synchronisieren über einen privaten Gist.
- Max kommuniziert auf Deutsch. App-Texte sind Deutsch, Übungssätze Englisch.

## Prüfungsformat (Moodle-Übungstest vom 24.11.2026 – „genau so wird die Prüfung aussehen“)
- Frage 1–6 (je 1 Punkt): englische Definition (Wörterbuch-Stil), darunter ein Satz mit einer Lücke. Bei mehreren Wörtern
  steht „(2 words)“ hinter der Definition; bei 2 von 6 steht der Anfangsbuchstabe vor dem Feld (dann nur den Rest tippen).
- Frage 7 (1 Punkt, von Hand bewertet): „Give the full form of the following word and explain it: USP“.
- Frage 8 (1 Punkt, von Hand bewertet): „Explain the following word: span of control“.
- Frage 9 (8 Punkte): zusammenhängender Text mit 8 Lücken, KEINE Hilfe (keine Definition, kein Buchstabe, keine Wortzahl).
- 16 Punkte, 10 Minuten. Gewertet wird exakt das Wort in der Form, die der Satz braucht („promoted“, „distribution channels“);
  ein Wort zu viel („foreign subsidiary“ statt „subsidiary“) ist falsch. Lücken können Teil eines Ausdrucks sein („[market] share“).
- Ergebnis von Max im Übungstest: Q1–6 2/6, Q9 5,3/8 (6 von 8 Lücken richtig – vermutlich Abzug oder 9. Lücke), Q7 ohne
  Erklärung, Q8 falsch. 6 der 16 Punkte kamen aus Wörtern, die damals nicht in der App waren (jetzt ergänzt).
- Typischer Fehler von Max: verwandtes Wort aus derselben Ecke (joint venture statt limited liability, assigned statt promoted,
  outbound logistics statt distribution channels, subsidiaries statt subordinates, senior management team statt headquarters).

## Vorgaben von Max (unbedingt einhalten)
- **Streng bleiben:** „der Tippfehler ist mein Fehler“ – Tippfehler zählen als Fehler.
  „mach es dadurch aber nicht leichter. es geht nur um wirkliche synonyme“ – als richtig gelten nur echte Synonyme.
  „aber halte es schwer“ – keine Anfangsbuchstaben als Standardhilfe.
- Lücken: seit 1.18 wie in der Prüfung mit englischer Definition über dem Satz (vorher 1.16: Striche je Buchstabe +
  Hinweis). Striche mit Anfangsbuchstaben gibt es nur noch über „Tipp“ (2. Stufe, zählt als Hilfe).
- „Arbeite genaustens alle Wörter heraus, die irgendwie relevant sein könnten“ – lieber vollständig als zu knapp.
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
  `H`: englische Hinweise (≤ 45 Zeichen, nur noch Reserve); `TEXTS`: 17 eigene Lückentexte je Buchaufgabe
  (`[[i]]` = Lücke für Eintrag i; Text „3.4“ deckt 3.4 und 3.5 ab). Einträge 155+ stehen im Block „ab 1.18“ am Ende.
- `src/definitions.py` (seit 1.18) – `D`: englische Definition je Eintrag (eigene Worte, verrät das Wort nicht);
  `ABBR`: 14 Abkürzungen für Frage 7 (Kurzform, Langformen, Musterantwort); `MTEXTS`: 15 Prüfungstexte mit genau 8 Lücken,
  `[[i|wort]]` = Lücke mit genau diesem Wort. build.py hängt `df`, `ab` an jeden Eintrag und `MTEXTS` an `TEXTS`.
- Weitere Felder in vocab.json: `sg` = Lückenwort des Prüfungssatzes, falls anders als `g`; `ga` = echte Synonyme, die in
  dieselbe Lücke passen (headquarters/head office, stock market/stock exchange, shareholders/stockholders).
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
TZ=Europe/Berlin node tests/engine.test.js          # "engine: 18 Testgruppen bestanden"
python3 -I tools/check_content.py                   # "510 Übungssätze, 17 Lückentexte + 15 Prüfungstexte, 255 von 255 …", 0 FEHLER
python3 -I build.py --html /pfad/index.html 1.18 21 # nur App-Seite zum Testen im Browser (Playwright ist gut dafür)
KEYSTORE=/pfad/key.jks KEYPASS=<von Max> python3 -I build.py 1.18 21 "Kurze Notiz für das Update-Banner"
jarsigner -verify dist/Vokabeltrainer.apk && python3 -I tools/dexcheck.py dist/Vokabeltrainer.apk
git -c user.name=Mymaxyt -c user.email=Mymaxyt@users.noreply.github.com commit -am "1.18: …"
git push
```
- Signierschlüssel: `key.jks`, Alias `max`. Max gibt Datei und Passwort direkt im Chat (nie committen).
  **Ohne genau diesen Schlüssel lässt sich kein Update über die installierte App spielen.**
- versionCode immer um 1 erhöhen (aktuell 24 → nächste 25). Die App vergleicht ihn mit `version.json`
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
- **Lücken streng wie Moodle:** `gapCheck(u, getippt, lückenwort)` – richtig nur das Lückenwort (plus BE/AE-Schreibung,
  Abkürzung ↔ Langform, `ga`-Synonyme). Ein anderes erlaubtes Wort der Einheit in falscher Form = Formfehler „f“.
  Schreiben (Deutsch → Englisch) nimmt weiter jede akzeptierte Form (`isRight`).
- `pick()` wählt die nächste Frage (Abstand: nicht unter den letzten 3 und < 2 Min. her), `modeFor` den Modus.
- Migration: alte 1.14-Stände über `absorbLegacy` als Modus `l`; `tidy()` fasst Duplikate (< 2 s) zusammen;
  Antworten, die heute erlaubt wären, werden nicht als Fehler übernommen.

## Prüfungssimulation (seit 1.18, template.html „Prüfungssimulation im Format des Moodle-Übungstests“)
- „Wie im Test“: 6× `def` (zufällige Einträge mit Prüfungssatz `s`, 2 einwortige mit Anfangsbuchstabe), 1× `abbr`, 1× `expl`
  (Wort ≤ 3 Wörter), 1× `text` (bevorzugt noch nicht gemachte M-Texte; Buchtexte mit mehr Lücken werden auf 8 gekürzt).
  10-Minuten-Timer, automatische Abgabe, Abgeben nur per Knopf mit zweitem Tippen, Enter springt zur nächsten Lücke.
- „Nur Lückentext“: ein Text mit allen Lücken, ohne Zeitlimit (Auswahl im Menü).
- Überprüfung wie Moodle (Richtig/Falsch/Teilweise, „Die richtige Antwort ist“), Frage 7/8 selbst bewerten (0/0,5/1;
  Langform wird automatisch geprüft). Seit 1.18.1 bewertet die App Frage 7/8 selbst vor (`autoGrade`: Abkürzung 0,5 für
  exakte Langform + 0,5 für Erklärung mit Kernwörtern der Musterlösung; Erklären 1/0,5/0 nach Anteil getroffener Kernwörter,
  unter 3 Wörtern = 0) – Max wollte „bewerte selbst“; die Knöpfe 0/0,5/1 bleiben zum Ändern. Ergebnis in `exams` {t, n: 16, p, o: offene Bewertungen, k, tx, d}.
- Sätze werden als Modus `x`, Textlücken als `t` im Verlauf gespeichert; Frage 7/8 nicht.
- Karteikarten haben die Richtung „Erklären“ (Wort/Abkürzung → englische Definition) als Übung für Frage 7/8.

## KI-Prüfung mit Claude (seit 1.19, Kachel „KI-Prüfung (Claude)“)
- Max will: „Antworten auf andere passende Wörter prüfen lassen“. Die App ruft die Anthropic-API direkt aus der WebView auf
  (`fetch` an api.anthropic.com mit Header `anthropic-dangerous-direct-browser-access: true`; CORS erlaubt das).
- **Eigener API-Schlüssel von Max** (getrennt vom Claude-Abo), in `localStorage.aiKey`/`aiKeyU`; seit 1.19.1 über den
  Ende-zu-Ende-verschlüsselten Geräte-Sync geteilt (Payload-Feld `ai: {k, u}`, neuerer gewinnt). NIE ins Repo/APK – die
  APK ist öffentlich, ein eingebauter Schlüssel wäre für jeden auslesbar. Max hat den Schlüssel im Chat genannt; er muss ihn
  selbst einmal in der App eintragen. Ohne Schlüssel verhält sich die App wie vorher.
- **Kosten niedrig halten (Vorgabe von Max):** alles mit `claude-haiku-5-5` (laut Presse 0,10 $/Mio. Eingabe, 0,50 $/Mio.
  Ausgabe), `thinking: {type: "disabled"}` (Haiku 5.5 denkt sonst standardmäßig und verdoppelt die Ausgabe-Token),
  `max_tokens` 160, nur bei falschen Antworten ohne Tippfehler. Eine Prüfung ≈ 300 Eingabe- + 70 Ausgabe-Token ≈ 0,007 Cent.
- Am 24.11. mit dem echten Schlüssel getestet (18 Fälle): develop/launch ✗, release/launch ✓, assigned/promoted ✗,
  consolidate ✗ (Wortart), voucher/coupon ✗, edge/competitive advantage ✓; Frage 7: Langform prüft die App exakt selbst,
  Claude bewertet nur die Erklärung (0/0,5).
- Lückensätze/Schreiben im Lernplan: falsche Antwort (nicht leer, kein Tippfehler „s“) → `aiGap` mit `claude-haiku-5-5`.
  Anerkannt → Punkt, aber Note 2 („mit Hilfe“), Wort kommt heute wieder; Hinweis, dass im echten Test vermutlich nur die
  Musterlösung zählt. Abgelehnt → Begründung von Claude unter der Lösung.
- Prüfungssimulation: nach der Abgabe prüft `aiReview` alle falschen Lücken und bewertet Frage 7/8 (`aiExplain`, 0/0,5/1); Ergebnis, Verlauf (Note 1 → 2) und Fehlerprotokoll (`ov: "KI"`) werden nachgezogen.
  Ohne Schlüssel/bei Fehlern greift die Stichwort-Vorbewertung `autoGrade`.
- Antwort an Max: Im echten Moodle-Test zählt nur, was der Dozent als Lösung hinterlegt hat (ggf. manuelle Nachkorrektur) –
  gleichwertige Wörter sind dort nicht sicher.

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
- **Annahmen einstellbar:** Punkte `settings.n` (seit 1.18 Standard 16 wie im Übungstest, Migration über `settings.f18`), Notenschlüssel `key1` (1,0 ab, Standard 95 %)
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
- 1.18 Prüfung genau im Format des Moodle-Übungstests; Lückensätze mit englischer Definition statt Strichen; strenge
  Lückenbewertung; 100 Wörter aus den Kursunterlagen; Karteikarten „Erklären“; Prognose auf 16 Punkte
- 1.19.1 KI günstiger (nur Haiku, ohne Nachdenken), fairere Synonym-Prüfung, Langform lokal geprüft, Schlüssel über Sync
- 1.19 KI-Prüfung mit Claude (eigener API-Schlüssel): gleichwertige Wörter anerkennen, Frage 7/8 bewerten
- 1.18.1 Frage 7/8 automatisch vorbewertet; Buchstabenvergleich in der Überprüfung repariert (stand untereinander)

## Offene Punkte / Ideen
- Prognose mit echten Daten von Max beobachten: Wie viele Abrufe über Nacht gibt es, wie weit weicht k von 1 ab?
- Notenschlüssel ist unbekannt (Standard 1,0 ab 95 %, 4,0 ab 50 %) – Max fragen, falls er ihn erfährt.
- Hörübung „Organisational structures“ fehlt – falls Max sie (oder ihre Wortliste) schickt, Wörter in K3 ergänzen.
- Bewertung von Frage 9 unklar (6 von 8 Lücken richtig = 5,3 Punkte): Abzug für Fehler oder 9. Lücke?
- Nach der Prüfung (26.11.) ggf. echte Note mit Prognose vergleichen und hier notieren.
