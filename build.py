"""Baut den Vokabeltrainer: App-HTML -> APK -> dist/ + version.json.

Aufruf:  KEYSTORE=/pfad/key.jks KEYPASS=... python3 build.py 1.11 12 "Kurzbeschreibung der Neuerungen"
Ohne KEYSTORE entsteht nur eine unsignierte APK (nicht installierbar).
Der Signierschlüssel gehört NICHT in dieses öffentliche Repo.
"""
import json, os, subprocess, sys, shutil, tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC, DIST = os.path.join(ROOT, "src"), os.path.join(ROOT, "dist")
REPO_RAW = "https://raw.githubusercontent.com/Mymaxyt/voctrainer/main"

def main():
    name, code, notes = sys.argv[1], int(sys.argv[2]), (sys.argv[3] if len(sys.argv) > 3 else "")
    data = json.load(open(os.path.join(SRC, "vocab.json"), encoding="utf-8"))
    html = open(os.path.join(SRC, "template.html"), encoding="utf-8").read()
    for ph, val in (("/*DATA*/[]", json.dumps(data, ensure_ascii=False)), ("/*VERSION_NAME*/", name), ("/*VERSION_CODE*/", str(code))):
        assert html.count(ph) == 1, ph
        html = html.replace(ph, val)
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
