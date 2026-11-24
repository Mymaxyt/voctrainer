"""Baut den Vokabeltrainer: App-HTML -> APK -> dist/ + version.json.

Aufruf:  KEYSTORE=/pfad/key.jks KEYPASS=... python3 build.py 1.15 16 "Kurzbeschreibung der Neuerungen"
         python3 build.py --html ziel.html      nur die App-Seite bauen (zum Testen im Browser)
         python3 build.py --data                Vokabeln mit Übungssätzen als JSON ausgeben (für die Tests)
Ohne KEYSTORE entsteht nur eine unsignierte APK (nicht installierbar).
Der Signierschlüssel gehört NICHT in dieses öffentliche Repo.
"""
import json, os, subprocess, sys, shutil, tempfile, importlib.util

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC, DIST = os.path.join(ROOT, "src"), os.path.join(ROOT, "dist")
REPO_RAW = "https://raw.githubusercontent.com/Mymaxyt/voctrainer/main"

def load_training():
    spec = importlib.util.spec_from_file_location("training", os.path.join(SRC, "training.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def load_module(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SRC, name + ".py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def load_data():
    data = json.load(open(os.path.join(SRC, "vocab.json"), encoding="utf-8"))
    tr, df = load_training(), load_module("definitions")
    for i, v in enumerate(data):
        v["t"] = [list(s) if isinstance(s, tuple) else s for s in tr.T[i]]
        v["h"] = tr.H[i]
        v["df"] = df.D[i]                                   # englische Definition (Prüfungsformat)
        if i in df.ABBR:
            ab, full, expl = df.ABBR[i]
            v["ab"] = {"a": ab, "f": full, "x": expl}       # Abkürzung ausschreiben und erklären
    return data, tr.TEXTS + df.MTEXTS

def js(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")

def make_html(name, code):
    data, texts = load_data()
    html = open(os.path.join(SRC, "template.html"), encoding="utf-8").read()
    engine = open(os.path.join(SRC, "engine.js"), encoding="utf-8").read()
    for ph, val in (("/*DATA*/[]", js(data)), ("/*TEXTS*/[]", js(texts)), ("/*ENGINE*/", engine),
                    ("/*VERSION_NAME*/", name), ("/*VERSION_CODE*/", str(code))):
        assert html.count(ph) == 1, ph
        html = html.replace(ph, val)
    return html

def main():
    if sys.argv[1:2] == ["--data"]:
        print(json.dumps(load_data()[0], ensure_ascii=False)); return
    if sys.argv[1:2] == ["--html"]:
        open(sys.argv[2], "w", encoding="utf-8").write(make_html(sys.argv[3] if len(sys.argv) > 3 else "test", sys.argv[4] if len(sys.argv) > 4 else 999))
        return
    name, code, notes = sys.argv[1], int(sys.argv[2]), (sys.argv[3] if len(sys.argv) > 3 else "")
    html = make_html(name, code)
    work = tempfile.mkdtemp()
    os.makedirs(os.path.join(work, "assets"))
    open(os.path.join(work, "assets", "index.html"), "w", encoding="utf-8").write(html)
    env = dict(os.environ, VERSION_CODE=str(code), VERSION_NAME=name)
    unsigned = os.path.join(work, "unsigned.apk")
    subprocess.run([sys.executable, "-I", os.path.join(SRC, "build_apk.py"), work, unsigned], check=True, env=env)
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, "Vokabeltrainer.apk")
    ks = os.environ.get("KEYSTORE")
    if not ks:
        shutil.copy(unsigned, out.replace(".apk", "-unsigned.apk")); print("WARNUNG: unsigniert"); return
    shutil.copy(unsigned, out)
    subprocess.run(["jarsigner", "-keystore", ks, "-storepass", os.environ["KEYPASS"], "-sigalg", "SHA256withRSA",
                    "-digestalg", "SHA-256", out, os.environ.get("KEYALIAS", "max")], check=True, stdout=subprocess.DEVNULL)
    json.dump({"versionCode": code, "versionName": name, "notes": notes,
               "apk": REPO_RAW + "/dist/Vokabeltrainer.apk"}, open(os.path.join(ROOT, "version.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("fertig:", out, os.path.getsize(out), "Bytes · version.json aktualisiert")

if __name__ == "__main__":
    main()
