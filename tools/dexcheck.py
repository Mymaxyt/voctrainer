"""Unabhängige Prüfung einer classes.dex: Struktur, Sortierung, Disassemblierung und Registertyp-Fluss (vereinfachter Verifier)."""
import struct, zlib, hashlib, sys, zipfile

def run(d):
    R = lambda f, o: struct.unpack_from("<" + f, d, o)
    errs = []
    def E(msg): errs.append(msg)
    if d[:8] != b"dex\n035\0": E("magic")
    if R("I", 8)[0] != zlib.adler32(d[12:]): E("checksum")
    if d[12:32] != hashlib.sha1(d[32:]).digest(): E("sha1")
    (fsz, hsz, endian, ls, lo, mapo, ns, so, nt, to, np_, po, nf, fo, nm, mo, nc, co, dsz, do) = R("20I", 32)
    if fsz != len(d) or do + dsz != len(d): E("sizes")
    def uleb(o):
        r = s = 0
        while True:
            b = d[o]; o += 1; r |= (b & 0x7F) << s; s += 7
            if not b & 0x80: return r, o
    def sleb(o):
        r = s = 0
        while True:
            b = d[o]; o += 1; r |= (b & 0x7F) << s; s += 7
            if not b & 0x80:
                if b & 0x40: r -= 1 << s
                return r, o
    def string(i):
        off = R("I", so + 4 * i)[0]; n, o = uleb(off); return d[o:d.index(b"\0", o)].decode()
    S = [string(i) for i in range(ns)]
    if S != sorted(S): E("strings unsorted")
    TI = [R("I", to + 4 * i)[0] for i in range(nt)]
    if TI != sorted(TI): E("types unsorted")
    T = [S[i] for i in TI]
    def tl(off):
        if not off: return []
        n = R("I", off)[0]; return [T[R("H", off + 4 + 2 * k)[0]] for k in range(n)]
    P = []
    for i in range(np_):
        sh, rt, pa = R("3I", po + 12 * i); P.append((S[sh], T[rt], tl(pa)))
        exp = "".join("L" if t[0] in "L[" else t for t in [T[rt]] + tl(pa))
        if S[sh] != exp: E(f"shorty {S[sh]} != {exp}")
    pkeys = [(TI.index(next(j for j in TI if S[j] == p[1])), [T.index(x) for x in p[2]]) for p in P]
    if pkeys != sorted(pkeys): E("protos unsorted")
    Fd = []
    for i in range(nf):
        c, t, n = R("HHI", fo + 8 * i); Fd.append((T[c], S[n], T[t], (c, n, t)))
    if [f[3] for f in Fd] != sorted(f[3] for f in Fd): E("fields unsorted")
    Md = []
    for i in range(nm):
        c, p, n = R("HHI", mo + 8 * i); Md.append((T[c], S[n], P[p][1], P[p][2], (c, n, p)))
    if [m[4] for m in Md] != sorted(m[4] for m in Md): E("methods unsorted")
    out = []
    defined = {}
    for ci in range(nc):
        cl, acc, sup, itf, src, ann, cdo, sv = R("8I", co + 32 * ci)
        out.append(f"class {T[cl]} extends {T[sup]} implements {tl(itf)} acc={hex(acc)}")
        o = cdo; sf, o = uleb(o); inf, o = uleb(o); dm, o = uleb(o); vm, o = uleb(o)
        fi = 0
        for k in range(sf + inf):
            df, o = uleb(o); fa, o = uleb(o); fi = df if k == 0 or k == sf else fi + df
            out.append(f"   field {Fd[fi][1]}: {Fd[fi][2]}")
        for kind, cnt in (("direct", dm), ("virtual", vm)):
            mi = 0
            for k in range(cnt):
                df, o = uleb(o); ma, o = uleb(o); cof, o = uleb(o); mi = df if k == 0 else mi + df
                defined[mi] = (kind, ma, cof, T[cl])
    for mi, (kind, ma, cof, cname) in sorted(defined.items()):
        c, name, ret, params, _ = Md[mi]
        static = bool(ma & 0x8)
        regs, ins, outs, tries, dbg, isz = R("4H2I", cof)
        w = [R("H", cof + 16 + 2 * k)[0] for k in range(isz)]
        out.append(f"{kind} {c}->{name}({''.join(params)}){ret} acc={hex(ma)} regs={regs} ins={ins} outs={outs} tries={tries}")
        exp_ins = sum(2 if p in "JD" else 1 for p in params) + (0 if static else 1)
        if ins != exp_ins: E(f"{name}: ins {ins} != {exp_ins}")
        # dekodieren
        insns, pc = {}, 0
        while pc < len(w):
            op = w[pc] & 0xFF; A8 = w[pc] >> 8
            if op == 0x0E: insns[pc] = ("return-void",); n = 1
            elif op == 0x12: insns[pc] = ("const/4", A8 & 0xF, ((A8 >> 4) ^ 8) - 8); n = 1
            elif op in (0x0A, 0x0B, 0x0C): insns[pc] = ({0x0A: "move-result", 0x0B: "move-result-wide", 0x0C: "move-result-object"}[op], A8); n = 1
            elif op == 0x13: insns[pc] = ("const/16", A8, w[pc + 1]); n = 2
            elif op == 0x16: insns[pc] = ("const-wide/16", A8, w[pc + 1]); n = 2
            elif op == 0x14: insns[pc] = ("const", A8, w[pc + 1] | (w[pc + 2] << 16)); n = 3
            elif op == 0x1A: insns[pc] = ("const-string", A8, S[w[pc + 1]]); n = 2
            elif op == 0x22: insns[pc] = ("new-instance", A8, T[w[pc + 1]]); n = 2
            elif op == 0x1F: insns[pc] = ("check-cast", A8, T[w[pc + 1]]); n = 2
            elif op in (0x53, 0x54, 0x5A, 0x5B): insns[pc] = ({0x53: "iget-wide", 0x54: "iget-object", 0x5A: "iput-wide", 0x5B: "iput-object"}[op], A8 & 0xF, A8 >> 4, Fd[w[pc + 1]]); n = 2
            elif op == 0x23: insns[pc] = ("new-array", A8 & 0xF, A8 >> 4, T[w[pc + 1]]); n = 2
            elif op == 0x4C: insns[pc] = ("aput-wide", A8, w[pc + 1] & 0xFF, w[pc + 1] >> 8); n = 2
            elif op in (0x38, 0x39): insns[pc] = ({0x38: "if-eqz", 0x39: "if-nez"}[op], A8, pc + ((w[pc + 1] ^ 0x8000) - 0x8000)); n = 2
            elif op in (0x32, 0x33): insns[pc] = ({0x32: "if-eq", 0x33: "if-ne"}[op], A8 & 0xF, A8 >> 4, pc + ((w[pc + 1] ^ 0x8000) - 0x8000)); n = 2
            elif op in (0x6E, 0x6F, 0x70, 0x71, 0x72):
                cnt = A8 >> 4; rr = [(w[pc + 2] >> (4 * j)) & 0xF for j in range(4)] + [A8 & 0xF]
                insns[pc] = ({0x6E: "invoke-virtual", 0x6F: "invoke-super", 0x70: "invoke-direct", 0x71: "invoke-static", 0x72: "invoke-interface"}[op], rr[:cnt], Md[w[pc + 1]]); n = 3
            else: E(f"{name}: unbekannter Opcode {hex(op)} @{pc}"); break
            pc += n
        starts = set(insns)
        # try-Bereiche
        handlers = []
        if tries:
            to_ = cof + 16 + 2 * isz + (2 if isz % 2 else 0)
            hl = to_ + 8 * tries
            for k in range(tries):
                st, cnt, ho = R("IHH", to_ + 8 * k)
                sz, o2 = sleb(hl + ho)
                if sz > 0: E("typed catch nicht erwartet")
                ca, _ = uleb(o2)
                for x in (st, st + cnt, ca):
                    if x not in starts and x != len(w): E(f"{name}: try-Grenze {x} keine Befehlsgrenze")
                handlers.append((st, st + cnt, ca))
                out.append(f"      try [{st},{st+cnt}) -> {ca}")
        for pc_, ins_ in sorted(insns.items()):
            out.append(f"      {pc_:3} {ins_[0]} " + " ".join(str(x) if not isinstance(x, tuple) else (f'{x[0]}->{x[1]}({"".join(x[2]) if isinstance(x[2], list) else x[2]})' if len(x) >= 4 and isinstance(x[3], list) else str(x[:3])) for x in ins_[1:]))
        # Typfluss
        params_regs = {}
        base = regs - ins
        r = base
        state0 = ["?"] * regs
        if not static:
            state0[r] = ("uninit-this", cname) if name == "<init>" else ("ref", cname); r += 1
        for p in params:
            if p in "JD": state0[r] = "long-lo"; state0[r + 1] = "long-hi"; r += 2
            elif p[0] in "L[": state0[r] = ("ref", p); r += 1
            else: state0[r] = "int"; r += 1
        def isref(v): return v == "zero" or (isinstance(v, tuple) and v[0] == "ref")
        def isint(v): return v in ("int", "zero")
        states = {0: state0}; work = [0]; last_ret = {}
        def flow(to, st):
            if to not in starts: E(f"{name}: Sprungziel {to} keine Befehlsgrenze"); return
            if to in states:
                old = states[to]; new = [a if a == b else "conflict" for a, b in zip(old, st)]
                if new != old: states[to] = new; work.append(to)
            else: states[to] = list(st); work.append(to)
        seen_guard = 0
        while work and seen_guard < 10000:
            seen_guard += 1
            pc_ = work.pop(); st = list(states[pc_]); ins_ = insns[pc_]; op = ins_[0]
            def need(reg, kind):
                v = st[reg] if reg < regs else "OOB"
                ok = {"ref": isref(v), "int": isint(v), "long": v == "long-lo" and reg + 1 < regs and st[reg + 1] == "long-hi"}[kind]
                if not ok: E(f"{name}@{pc_} {op}: v{reg} ist {v}, erwartet {kind}")
            for h0, h1, ca in handlers:
                if h0 <= pc_ < h1: flow(ca, st)
            nxt = pc_ + {1: 1}.get(0, 0)
            size = {"return-void": 1, "const/4": 1, "move-result": 1, "move-result-wide": 1, "move-result-object": 1, "const": 3}.get(op, 3 if op.startswith("invoke") else 2)
            nxt = pc_ + size
            pending = last_ret.pop(pc_, None)
            if op == "return-void":
                if name == "<init>" and any(isinstance(v, tuple) and v[0] == "uninit-this" for v in st): E(f"{name}: this nicht initialisiert")
                continue
            if op.startswith("move-result"):
                prev = states.get(("ret", pc_))
                if prev is None: E(f"{name}@{pc_}: move-result ohne direkt vorangehendes invoke")
                else:
                    if op == "move-result-wide":
                        if prev != "J": E(f"{name}@{pc_}: move-result-wide nach {prev}")
                        st[ins_[1]] = "long-lo"; st[ins_[1] + 1] = "long-hi"
                    elif op == "move-result-object":
                        if prev[0] not in "L[": E(f"{name}@{pc_}: move-result-object nach {prev}")
                        st[ins_[1]] = ("ref", prev)
                    else:
                        if prev not in "IZBSC": E(f"{name}@{pc_}: move-result nach {prev}")
                        st[ins_[1]] = "int"
                flow(nxt, st); continue
            if op == "const/4" or op == "const/16" or op == "const":
                st[ins_[1]] = "zero" if ins_[2] == 0 else "int"
            elif op == "const-wide/16": st[ins_[1]] = "long-lo"; st[ins_[1] + 1] = "long-hi"
            elif op == "const-string": st[ins_[1]] = ("ref", "Ljava/lang/String;")
            elif op == "new-instance": st[ins_[1]] = ("uninit", ins_[2])
            elif op == "check-cast": need(ins_[1], "ref"); st[ins_[1]] = ("ref", ins_[2])
            elif op == "new-array": need(ins_[2], "int"); st[ins_[1]] = ("ref", ins_[3])
            elif op == "aput-wide": need(ins_[1], "long"); need(ins_[2], "ref"); need(ins_[3], "int")
            elif op in ("iget-object", "iget-wide", "iput-object", "iput-wide"):
                need(ins_[2], "ref"); f = ins_[3]
                if op == "iget-object": st[ins_[1]] = ("ref", f[2])
                elif op == "iget-wide": st[ins_[1]] = "long-lo"; st[ins_[1] + 1] = "long-hi"
                elif op == "iput-object": need(ins_[1], "ref")
                else: need(ins_[1], "long")
                if (op.endswith("wide")) != (f[2] == "J"): E(f"{name}@{pc_}: {op} auf Feld {f[1]}:{f[2]}")
            elif op in ("if-eqz", "if-nez"):
                v = st[ins_[1]]
                if not (isint(v) or isref(v)): E(f"{name}@{pc_}: {op} auf {v}")
                flow(ins_[2], st)
            elif op in ("if-eq", "if-ne"): need(ins_[1], "int"); need(ins_[2], "int"); flow(ins_[3], st)
            elif op.startswith("invoke"):
                regs_, m = ins_[1], ins_[2]
                mc, mn, mr, mp = m[0], m[1], m[2], m[3]
                k = 0
                if op != "invoke-static":
                    v = st[regs_[0]]
                    if mn == "<init>":
                        if not (isinstance(v, tuple) and v[0] in ("uninit", "uninit-this")): E(f"{name}@{pc_}: <init> auf {v}")
                        else:
                            newv = ("ref", v[1]); st = [newv if x == v else x for x in st]
                    elif not isref(v) or v == "zero": E(f"{name}@{pc_}: Empfänger v{regs_[0]} ist {v}")
                    k = 1
                for p in mp:
                    if p in "JD":
                        if not (st[regs_[k]] == "long-lo" and st[regs_[k + 1]] == "long-hi" and regs_[k + 1] == regs_[k] + 1): E(f"{name}@{pc_}: long-Arg v{regs_[k]}")
                        k += 2
                    elif p[0] in "L[":
                        v = st[regs_[k]]
                        if not isref(v): E(f"{name}@{pc_}: Arg v{regs_[k]} ist {v}, erwartet {p}")
                        k += 1
                    else:
                        if not isint(st[regs_[k]]): E(f"{name}@{pc_}: Arg v{regs_[k]} ist {st[regs_[k]]}, erwartet {p}")
                        k += 1
                if k != len(regs_): E(f"{name}@{pc_}: Argumentanzahl")
                if len(regs_) > outs: E(f"{name}@{pc_}: outs zu klein")
                if mr != "V" and nxt in insns and insns[nxt][0].startswith("move-result"): states[("ret", nxt)] = mr
                st = st
            for i_, v in enumerate(st):
                pass
            flow(nxt, st)
        for pc_ in insns:
            if pc_ not in states: E(f"{name}@{pc_}: unerreichbarer Code")
        for pc_, ins_ in insns.items():
            for x in ins_[1:]:
                if isinstance(x, int) and ins_[0] not in ("const/4", "const/16", "const-wide/16", "const") and not ins_[0].startswith("if") and x >= regs: E(f"{name}@{pc_}: Register v{x} >= {regs}")
    return out, errs

if __name__ == "__main__":
    src = sys.argv[1]
    d = zipfile.ZipFile(src).read("classes.dex") if src.endswith(".apk") else open(src, "rb").read()
    out, errs = run(d)
    if "-v" in sys.argv: print("\n".join(out))
    print("FEHLER:" if errs else "Keine Fehler gefunden.", *errs, sep="\n  ")
