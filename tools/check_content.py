"""Prüft Übungssätze und Lückentexte (src/training.py) gegen vocab.json.

Fehler (Abbruch): fehlende/doppelte Sätze, keine oder mehrere Lücken, Prüfungssatz wiederverwendet,
Lückentexte ohne vollständige Abdeckung. Hinweise: Lösungswort steht schon im Satz, a/an passt nicht.
Aufruf: python3 tools/check_content.py
"""
import json, os, re, sys, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, "src", "vocab.json"), encoding="utf-8"))
spec = importlib.util.spec_from_file_location("training", os.path.join(ROOT, "src", "training.py"))
tr = importlib.util.module_from_spec(spec); spec.loader.exec_module(tr)

FUNC = {"a", "an", "the", "of", "to", "in", "from", "for", "and", "on", "at", "by"}
errors, hints = [], []

def tokens(s):
    return [w for w in re.findall(r"[a-z0-9&]+", re.sub(r"\([^)]*\)", " ", s.lower())) if w not in FUNC and len(w) > 2]

def variants(w):
    out = {w, w + "s", w + "es"}
    if w.endswith("s"): out.add(w[:-1])
    if w.endswith("ies"): out.add(w[:-3] + "y")
    return out

def leaks(answer_forms, text):
    words = set(re.findall(r"[a-z0-9&]+", text.lower()))
    hit = set()
    for f in answer_forms:
        for t in tokens(f):
            if variants(t) & words: hit.add(t)
    return hit

def forms(v):
    return [v["e"], v["g"], *v["a"]]

def article(before, answer):
    m = re.search(r"\b(a|an)\s*$", before, re.I)
    if not m: return None
    vowel = answer[0].lower() in "aeiou" and not answer.lower().startswith(("usp", "uni", "eu"))
    if m.group(1).lower() == "a" and vowel: return "„a“ vor Vokal"
    if m.group(1).lower() == "an" and not vowel: return "„an“ vor Konsonant"
    return None

seen = {}
exam = {v["s"].strip().lower() for v in data}
if sorted(tr.T) != list(range(len(data))): errors.append("T hat nicht genau die Einträge 0–%d" % (len(data) - 1))
for i, pair in sorted(tr.T.items()):
    v = data[i]
    if len(pair) != 2: errors.append(f"{i}: nicht genau zwei Sätze")
    for s in pair:
        sent, ans = (s if isinstance(s, tuple) else (s, v["g"]))
        if sent.count("___") != 1: errors.append(f"{i}: {sent!r} braucht genau eine Lücke")
        key = sent.strip().lower()
        if key in exam: errors.append(f"{i}: Prüfungssatz wiederverwendet: {sent}")
        if key in seen: errors.append(f"{i}: doppelt mit {seen[key]}: {sent}")
        seen[key] = i
        rest = sent.replace("___", " ")
        lk = leaks(forms(v), rest)
        if lk: hints.append(f"{i} {v['e']}: Lösungswort im Satz ({', '.join(sorted(lk))}): {sent}")
        a = article(sent.split("___")[0], ans)
        if a: hints.append(f"{i} {v['e']}: {a}: {sent}")

# Hinweise in Klammern
if sorted(getattr(tr, "H", {})) != list(range(len(data))): errors.append("H hat nicht genau die Einträge 0–%d" % (len(data) - 1))
for i, h in sorted(getattr(tr, "H", {}).items()):
    lk = leaks(forms(data[i]), h)
    if lk: errors.append(f"{i} {data[i]['e']}: Hinweis verrät das Lösungswort ({', '.join(sorted(lk))}): {h}")
    if not h.strip() or len(h) > 45: errors.append(f"{i} {data[i]['e']}: Hinweis leer oder zu lang: {h}")

# Lückentexte
used = {}
for t in tr.TEXTS:
    ids = [int(x) for x in re.findall(r"\[\[(\d+)\]\]", t["text"])]
    prefix = t["id"]
    for i in ids:
        if i in used: errors.append(f"Text {prefix}: Eintrag {i} schon in Text {used[i]}")
        used[i] = prefix
        n = data[i]["n"]
        if not (n.startswith(prefix + "-") or (prefix == "3.4" and n.startswith("3.5-"))):
            errors.append(f"Text {prefix}: Eintrag {i} ({n}) gehört nicht zu dieser Aufgabe")
        plain = re.sub(r"\[\[\d+\]\]", " ", t["text"])
        lk = leaks(forms(data[i]), plain)
        if lk: hints.append(f"Text {prefix} [[{i}]] {data[i]['e']}: Lösungswort im Text ({', '.join(sorted(lk))})")
        before = t["text"].split(f"[[{i}]]")[0]
        a = article(before, data[i]["g"])
        if a: hints.append(f"Text {prefix} [[{i}]] {data[i]['e']}: {a}")
missing = sorted(set(range(len(data))) - set(used))
if missing: errors.append(f"Lückentexte: Einträge fehlen: {missing}")

print(f"{len(seen)} Übungssätze, {len(tr.TEXTS)} Lückentexte mit {len(used)} Lücken")
for h in hints: print("Hinweis:", h)
for e in errors: print("FEHLER:", e)
sys.exit(1 if errors else 0)
