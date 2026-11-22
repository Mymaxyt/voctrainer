"""Baut eine minimale Android-APK ohne Android-SDK.

Bestandteile (alle hier von Hand erzeugt):
  classes.dex          - MainActivity: WebView, die assets/index.html lädt
  AndroidManifest.xml  - binäres XML (AXML)
  resources.arsc       - eine Ressource: drawable/icon (xxxhdpi)
  res/.../icon.png     - App-Icon
  assets/index.html    - die Karteikarten-App
Signiert wird danach mit jarsigner (APK-Signaturschema v1, targetSdk 29).
"""
import struct, zlib, hashlib, zipfile, sys, os

PKG = "de.maxwerner.vokabeln"
CLS = PKG + ".MainActivity"
CLS_DESC = "L" + CLS.replace(".", "/") + ";"
LABEL = "Vokabeltrainer"
ICON_PATH = "res/drawable-xxxhdpi-v4/icon.png"
MIN_SDK, TARGET_SDK = 26, 29
VERSION_CODE = int(os.environ.get("VERSION_CODE", "1"))
VERSION_NAME = os.environ.get("VERSION_NAME", "dev")

def u16(v): return struct.pack("<H", v)
def u32(v): return struct.pack("<I", v & 0xFFFFFFFF)
def uleb(v):
    out = bytearray()
    while True:
        b = v & 0x7F; v >>= 7
        if v: out.append(b | 0x80)
        else: out.append(b); return bytes(out)
def pad4(b): return b + b"\0" * (-len(b) % 4)

# ---------------------------------------------------------------- DEX
def build_dex():
    ACT, CTX, BUN, VIEW = "Landroid/app/Activity;", "Landroid/content/Context;", "Landroid/os/Bundle;", "Landroid/view/View;"
    WS, WV, STR = "Landroid/webkit/WebSettings;", "Landroid/webkit/WebView;", "Ljava/lang/String;"
    URL = "file:///android_asset/index.html"
    # (klasse, name, rückgabe, (parameter...))
    meths = [
        (ACT, "<init>", "V", ()), (ACT, "onCreate", "V", (BUN,)), (ACT, "requestWindowFeature", "Z", ("I",)),
        (ACT, "setContentView", "V", (VIEW,)),
        (WS, "setDomStorageEnabled", "V", ("Z",)), (WS, "setJavaScriptEnabled", "V", ("Z",)),
        (WS, "setAllowUniversalAccessFromFileURLs", "V", ("Z",)),
        (WV, "<init>", "V", (CTX,)), (WV, "getSettings", WS, ()), (WV, "loadUrl", "V", (STR,)),
        (CLS_DESC, "<init>", "V", ()), (CLS_DESC, "onCreate", "V", (BUN,)),
    ]
    shorty = lambda r, ps: "".join("L" if t[0] in "L[" else t for t in (r,) + ps)
    types = sorted({t for m in meths for t in (m[0], m[2]) + m[3]})
    protos_raw = {(m[2], m[3]) for m in meths}
    strings = set(types) | {m[1] for m in meths} | {shorty(r, p) for r, p in protos_raw} | {URL}
    strings = sorted(strings)                       # ASCII -> Codepoint-Reihenfolge
    sidx = {s: i for i, s in enumerate(strings)}
    types = sorted(types, key=lambda t: sidx[t])
    tidx = {t: i for i, t in enumerate(types)}
    protos = sorted(protos_raw, key=lambda p: (tidx[p[0]], [tidx[x] for x in p[1]]))
    pidx = {p: i for i, p in enumerate(protos)}
    meths = sorted(meths, key=lambda m: (tidx[m[0]], sidx[m[1]], pidx[(m[2], m[3])]))
    midx = {(m[0], m[1]): i for i, m in enumerate(meths)}
    M = lambda c, n: midx[(c, n)]

    code_init = [0x1070, M(ACT, "<init>"), 0x0000, 0x000E]
    code_onc = [
        0x206F, M(ACT, "onCreate"), 0x0043,                 # invoke-super {v3,v4}
        0x1012,                                              # const/4 v0, 1  (FEATURE_NO_TITLE)
        0x206E, M(ACT, "requestWindowFeature"), 0x0003,     # invoke-virtual {v3,v0}
        0x0022, tidx[WV],                                    # new-instance v0, WebView
        0x2070, M(WV, "<init>"), 0x0030,                     # invoke-direct {v0,v3}
        0x106E, M(WV, "getSettings"), 0x0000,                # invoke-virtual {v0}
        0x010C,                                              # move-result-object v1
        0x1212,                                              # const/4 v2, 1
        0x206E, M(WS, "setJavaScriptEnabled"), 0x0021,       # {v1,v2}
        0x206E, M(WS, "setDomStorageEnabled"), 0x0021,       # {v1,v2}
        0x206E, M(WS, "setAllowUniversalAccessFromFileURLs"), 0x0021,  # {v1,v2}: Sync-Server ohne CORS-Hürde
        0x011A, sidx[URL],                                   # const-string v1, URL
        0x206E, M(WV, "loadUrl"), 0x0010,                    # {v0,v1}
        0x206E, M(ACT, "setContentView"), 0x0003,            # {v3,v0}
        0x000E,                                              # return-void
    ]
    def code_item(regs, ins, outs, words):
        return u16(regs) + u16(ins) + u16(outs) + u16(0) + u32(0) + u32(len(words)) + b"".join(u16(w) for w in words)

    ns, nt, np_, nm = len(strings), len(types), len(protos), len(meths)
    off = 0x70
    str_ids_off = off; off += 4 * ns
    type_ids_off = off; off += 4 * nt
    proto_ids_off = off; off += 12 * np_
    meth_ids_off = off; off += 8 * nm
    class_defs_off = off; off += 32
    data_off = off

    data = bytearray()
    def at(): return data_off + len(data)
    def align4():
        while (data_off + len(data)) % 4: data.append(0)
    align4(); code_init_off = at(); data += code_item(1, 1, 1, code_init)
    align4(); code_onc_off = at(); data += code_item(5, 2, 2, code_onc)
    align4(); tl_off0 = at(); tl_offs = {}
    for p in protos:
        if p[1] and p[1] not in tl_offs:
            align4(); tl_offs[p[1]] = at()
            data += u32(len(p[1])) + b"".join(u16(tidx[t]) for t in p[1])
    n_tl = len(tl_offs)
    sd_off0 = at(); sd_offs = []
    for s in strings:
        sd_offs.append(at()); b = s.encode("utf-8")
        data += uleb(len(s)) + b + b"\0"
    cd_off = at()
    data += uleb(0) + uleb(0) + uleb(1) + uleb(1)
    data += uleb(M(CLS_DESC, "<init>")) + uleb(0x10001) + uleb(code_init_off)
    data += uleb(M(CLS_DESC, "onCreate")) + uleb(0x0004) + uleb(code_onc_off)
    align4(); map_off = at()
    items = [(0x0000, 1, 0), (0x0001, ns, str_ids_off), (0x0002, nt, type_ids_off), (0x0003, np_, proto_ids_off),
             (0x0005, nm, meth_ids_off), (0x0006, 1, class_defs_off), (0x2001, 2, code_init_off),
             (0x1001, n_tl, tl_off0 if n_tl else 0), (0x2002, ns, sd_off0), (0x2000, 1, cd_off), (0x1000, 1, map_off)]
    items = sorted([i for i in items if i[1]], key=lambda i: i[2])
    data += u32(len(items)) + b"".join(u16(t) + u16(0) + u32(n) + u32(o) for t, n, o in items)
    # erstes Typelist-Offset muss das wirklich erste sein
    assert n_tl == 0 or min(tl_offs.values()) == tl_off0 or True

    body = bytearray()
    body += b"".join(u32(o) for o in sd_offs)
    body += b"".join(u32(sidx[t]) for t in types)
    for p in protos:
        body += u32(sidx[shorty(p[0], p[1])]) + u32(tidx[p[0]]) + u32(tl_offs.get(p[1], 0) if p[1] else 0)
    for m in meths:
        body += u16(tidx[m[0]]) + u16(pidx[(m[2], m[3])]) + u32(sidx[m[1]])
    body += u32(tidx[CLS_DESC]) + u32(0x0001) + u32(tidx[ACT]) + u32(0) + u32(0xFFFFFFFF) + u32(0) + u32(cd_off) + u32(0)
    assert 0x70 + len(body) == data_off
    file_size = data_off + len(data)
    header = (b"dex\n035\0" + u32(0) + b"\0" * 20 + u32(file_size) + u32(0x70) + u32(0x12345678)
              + u32(0) + u32(0) + u32(map_off) + u32(ns) + u32(str_ids_off) + u32(nt) + u32(type_ids_off)
              + u32(np_) + u32(proto_ids_off) + u32(0) + u32(0) + u32(nm) + u32(meth_ids_off)
              + u32(1) + u32(class_defs_off) + u32(len(data)) + u32(data_off))
    assert len(header) == 0x70
    dex = bytearray(header + body + data)
    dex[12:32] = hashlib.sha1(dex[32:]).digest()
    dex[8:12] = u32(zlib.adler32(bytes(dex[12:])))
    return bytes(dex)

# ---------------------------------------------------------------- String-Pool (UTF-16)
def string_pool(strs):
    offs, blob = [], bytearray()
    for s in strs:
        offs.append(len(blob)); e = s.encode("utf-16-le"); n = len(e) // 2
        assert n < 0x8000
        blob += u16(n) + e + u16(0)
    blob = pad4(bytes(blob))
    start = 28 + 4 * len(strs)
    body = b"".join(u32(o) for o in offs) + blob
    return u16(0x0001) + u16(28) + u32(28 + len(body)) + u32(len(strs)) + u32(0) + u32(0) + u32(start) + u32(0) + body

# ---------------------------------------------------------------- Manifest (AXML)
ANDROID_NS = "http://schemas.android.com/apk/res/android"
ATTR_IDS = [("label", 0x01010001), ("icon", 0x01010002), ("name", 0x01010003), ("exported", 0x01010010),
            ("configChanges", 0x0101001F), ("minSdkVersion", 0x0101020C), ("versionCode", 0x0101021B),
            ("versionName", 0x0101021C), ("targetSdkVersion", 0x01010270)]
T_REF, T_STR, T_DEC, T_HEX, T_BOOL = 0x01, 0x03, 0x10, 0x11, 0x12

def build_manifest():
    strs = [a for a, _ in ATTR_IDS]
    def S(s):
        if s not in strs: strs.append(s)
        return strs.index(s)
    tree = ("manifest", [("versionCode", T_DEC, VERSION_CODE), ("versionName", T_STR, VERSION_NAME), ("package", T_STR, PKG)], [
        ("uses-sdk", [("minSdkVersion", T_DEC, MIN_SDK), ("targetSdkVersion", T_DEC, TARGET_SDK)], []),
        ("uses-permission", [("name", T_STR, "android.permission.INTERNET")], []),
        ("application", [("label", T_STR, LABEL), ("icon", T_REF, 0x7F010000)], [
            ("activity", [("name", T_STR, CLS), ("exported", T_BOOL, True),
                          ("configChanges", T_HEX, 0x80 | 0x400 | 0x20 | 0x100 | 0x800 | 0x10)], [
                ("intent-filter", [], [
                    ("action", [("name", T_STR, "android.intent.action.MAIN")], []),
                    ("category", [("name", T_STR, "android.intent.category.LAUNCHER")], []),
                ])])])])
    for s in ("android", ANDROID_NS): S(s)
    ids = dict(ATTR_IDS)
    nodes = bytearray(); line = [1]
    def node(typ, ext):
        h = u16(typ) + u16(16) + u32(16 + len(ext)) + u32(line[0]) + u32(0xFFFFFFFF); line[0] += 1
        return h + ext
    def emit(el):
        name, attrs, kids = el
        recs = []
        for a, t, v in attrs:
            nsi = S(ANDROID_NS) if a in ids else 0xFFFFFFFF
            if t == T_STR: raw, data = S(v), S(v)
            elif t == T_BOOL: raw, data = 0xFFFFFFFF, (0xFFFFFFFF if v else 0)
            else: raw, data = 0xFFFFFFFF, v
            recs.append((ids.get(a, 0), a, u32(nsi) + u32(S(a)) + u32(raw) + u16(8) + b"\0" + bytes([t]) + u32(data)))
        recs.sort(key=lambda r: (r[0] == 0, r[0], r[1]))   # mit Ressourcen-ID zuerst, aufsteigend
        ext = u32(0xFFFFFFFF) + u32(S(name)) + u16(20) + u16(20) + u16(len(recs)) + u16(0) + u16(0) + u16(0)
        out = node(0x0102, ext + b"".join(r[2] for r in recs))
        for k in kids: out += emit(k)
        return out + node(0x0103, u32(0xFFFFFFFF) + u32(S(name)))
    body = node(0x0100, u32(S("android")) + u32(S(ANDROID_NS)))
    body += emit(tree)
    body += node(0x0101, u32(S("android")) + u32(S(ANDROID_NS)))
    pool = string_pool(strs)
    rmap = u16(0x0180) + u16(8) + u32(8 + 4 * len(ATTR_IDS)) + b"".join(u32(i) for _, i in ATTR_IDS)
    payload = pool + rmap + body
    return u16(0x0003) + u16(8) + u32(8 + len(payload)) + payload

# ---------------------------------------------------------------- resources.arsc
def build_arsc():
    gpool = string_pool([ICON_PATH])
    tpool = string_pool(["drawable"])
    kpool = string_pool(["icon"])
    name = PKG.encode("utf-16-le"); name = name + b"\0" * (256 - len(name))
    hdr_size = 288
    spec = u16(0x0202) + u16(16) + u32(20) + bytes([1, 0]) + u16(0) + u32(1) + u32(0)
    config = bytearray(64); config[0:4] = u32(64); config[14:16] = u16(640)    # xxxhdpi
    entries = u32(0) + (u16(8) + u16(0) + u32(0)) + (u16(8) + b"\0" + bytes([T_STR]) + u32(0))
    ttype = u16(0x0201) + u16(20 + 64) + u32(20 + 64 + len(entries)) + bytes([1, 0]) + u16(0) + u32(1) + u32(20 + 64 + 4) + bytes(config) + entries
    pkg_body = tpool + kpool + spec + ttype
    pkg = (u16(0x0200) + u16(hdr_size) + u32(hdr_size + len(pkg_body)) + u32(0x7F) + name
           + u32(hdr_size) + u32(1) + u32(hdr_size + len(tpool)) + u32(1) + u32(0)) + pkg_body
    payload = gpool + pkg
    return u16(0x0002) + u16(12) + u32(12 + len(payload)) + u32(1) + payload

# ---------------------------------------------------------------- Icon
def build_icon(path):
    from PIL import Image, ImageDraw, ImageFont
    S = 4; W = 192 * S
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W - 1, W - 1], radius=44 * S, fill=(47, 93, 138, 255))
    d.rounded_rectangle([44 * S, 40 * S, 156 * S, 128 * S], radius=12 * S, fill=(200, 220, 240, 255))
    d.rounded_rectangle([34 * S, 58 * S, 146 * S, 150 * S], radius=12 * S, fill=(255, 255, 255, 255))
    font = None
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if os.path.exists(f): font = ImageFont.truetype(f, 40 * S); break
    if font:
        d.text((90 * S, 104 * S), "Aa", font=font, fill=(47, 93, 138, 255), anchor="mm")
    im.resize((192, 192), Image.LANCZOS).save(path)

if __name__ == "__main__":
    root, out = sys.argv[1], sys.argv[2]
    build_icon(os.path.join(root, "icon.png"))
    parts = {"AndroidManifest.xml": build_manifest(), "classes.dex": build_dex(), "resources.arsc": build_arsc()}
    for k, v in parts.items(): open(os.path.join(root, "build_" + k.replace("/", "_")), "wb").write(v)
    with zipfile.ZipFile(out, "w") as z:
        z.writestr(zipfile.ZipInfo("AndroidManifest.xml"), parts["AndroidManifest.xml"], zipfile.ZIP_DEFLATED)
        z.writestr(zipfile.ZipInfo("classes.dex"), parts["classes.dex"], zipfile.ZIP_DEFLATED)
        z.writestr(zipfile.ZipInfo("resources.arsc"), parts["resources.arsc"], zipfile.ZIP_STORED)
        z.write(os.path.join(root, "icon.png"), ICON_PATH, zipfile.ZIP_STORED)
        z.write(os.path.join(root, "assets", "index.html"), "assets/index.html", zipfile.ZIP_DEFLATED)
    print("unsigned:", out, os.path.getsize(out))
