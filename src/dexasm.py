"""Kleiner Dalvik-Assembler: erzeugt eine classes.dex (Version 035) aus Klassen-Beschreibungen.

Unterstützt genau die Befehle, die der Vokabeltrainer braucht. Registerangaben sind Zahlen (v0, v1, …);
Parameter liegen wie in Dalvik üblich in den letzten Registern (this zuerst).
"""
import struct, zlib, hashlib

def u16(v): return struct.pack("<H", v & 0xFFFF)
def u32(v): return struct.pack("<I", v & 0xFFFFFFFF)
def uleb(v):
    out = bytearray()
    while True:
        b = v & 0x7F; v >>= 7
        if v: out.append(b | 0x80)
        else: out.append(b); return bytes(out)
def sleb(v):
    out = bytearray()
    while True:
        b = v & 0x7F; v >>= 7
        done = (v == 0 and not b & 0x40) or (v == -1 and b & 0x40)
        out.append(b if done else b | 0x80)
        if done: return bytes(out)

SIZE = {"return-void": 1, "const/4": 1, "move-result": 1, "move-result-wide": 1, "move-result-object": 1,
        "const/16": 2, "const-wide/16": 2, "const": 3, "const-string": 2, "new-instance": 2, "check-cast": 2,
        "iget-object": 2, "iput-object": 2, "iget-wide": 2, "iput-wide": 2, "new-array": 2, "aput-wide": 2,
        "if-eqz": 2, "if-nez": 2, "if-eq": 2, "if-ne": 2,
        "invoke-virtual": 3, "invoke-super": 3, "invoke-direct": 3, "invoke-static": 3, "invoke-interface": 3}
INVOKE = {"invoke-virtual": 0x6E, "invoke-super": 0x6F, "invoke-direct": 0x70, "invoke-static": 0x71, "invoke-interface": 0x72}
FIELD = {"iget-object": 0x54, "iput-object": 0x5B, "iget-wide": 0x53, "iput-wide": 0x5A}

def shorty(ret, params): return "".join("L" if t[0] in "L[" else t for t in (ret,) + tuple(params))
def words(params): return sum(2 if t in ("J", "D") else 1 for t in params)

def build(classes):
    """classes: [{name, super, interfaces, fields:[(name,type,acc)], methods:[{name,ret,params,acc,static,regs,code,tries}]}]"""
    strings, types, protos, fields, meths = set(), set(), set(), set(), set()
    def T(t): types.add(t); strings.add(t)
    def P(ret, params): T(ret); [T(p) for p in params]; strings.add(shorty(ret, params)); protos.add((ret, tuple(params)))
    def M(c, n, ret, params): T(c); strings.add(n); P(ret, params); meths.add((c, n, ret, tuple(params)))
    def F(c, n, t): T(c); T(t); strings.add(n); fields.add((c, n, t))
    for cl in classes:
        T(cl["name"]); T(cl["super"]); [T(i) for i in cl.get("interfaces", [])]
        for n, t, _ in cl.get("fields", []): F(cl["name"], n, t)
        for m in cl["methods"]:
            M(cl["name"], m["name"], m["ret"], m["params"])
            for ins in m["code"]:
                if not isinstance(ins, tuple): continue
                op = ins[0]
                if op == "const-string": strings.add(ins[2])
                elif op in ("new-instance", "check-cast"): T(ins[2])
                elif op == "new-array": T(ins[3])
                elif op in FIELD: F(*ins[3])
                elif op in INVOKE: M(*ins[2])
    S = sorted(strings); sidx = {s: i for i, s in enumerate(S)}
    TY = sorted(types, key=lambda t: sidx[t]); tidx = {t: i for i, t in enumerate(TY)}
    PR = sorted(protos, key=lambda p: (tidx[p[0]], [tidx[x] for x in p[1]])); pidx = {p: i for i, p in enumerate(PR)}
    FL = sorted(fields, key=lambda f: (tidx[f[0]], sidx[f[1]], tidx[f[2]])); fidx = {f: i for i, f in enumerate(FL)}
    ME = sorted(meths, key=lambda m: (tidx[m[0]], sidx[m[1]], pidx[(m[2], m[3])])); midx = {m: i for i, m in enumerate(ME)}

    def assemble(m, cls):
        labels, pc = {}, 0
        for ins in m["code"]:
            if isinstance(ins, str): labels[ins] = pc
            else: pc += SIZE[ins[0]]
        out, pc, outs = [], 0, 0
        for ins in m["code"]:
            if isinstance(ins, str): continue
            op, a = ins[0], ins[1:]
            if op == "return-void": w = [0x000E]
            elif op == "const/4": assert -8 <= a[1] < 8; w = [((a[1] & 0xF) << 12) | (a[0] << 8) | 0x12]
            elif op.startswith("move-result"): w = [(a[0] << 8) | {"move-result": 0x0A, "move-result-wide": 0x0B, "move-result-object": 0x0C}[op]]
            elif op == "const/16": w = [(a[0] << 8) | 0x13, a[1]]
            elif op == "const-wide/16": w = [(a[0] << 8) | 0x16, a[1]]
            elif op == "const": w = [(a[0] << 8) | 0x14, a[1] & 0xFFFF, (a[1] >> 16) & 0xFFFF]
            elif op == "const-string": w = [(a[0] << 8) | 0x1A, sidx[a[1]]]
            elif op == "new-instance": w = [(a[0] << 8) | 0x22, tidx[a[1]]]
            elif op == "check-cast": w = [(a[0] << 8) | 0x1F, tidx[a[1]]]
            elif op in FIELD: assert a[0] < 16 and a[1] < 16; w = [(a[1] << 12) | (a[0] << 8) | FIELD[op], fidx[a[2]]]
            elif op == "new-array": w = [(a[1] << 12) | (a[0] << 8) | 0x23, tidx[a[2]]]
            elif op == "aput-wide": w = [(a[0] << 8) | 0x4C, (a[2] << 8) | a[1]]
            elif op in ("if-eqz", "if-nez"): w = [(a[0] << 8) | (0x38 if op == "if-eqz" else 0x39), (labels[a[1]] - pc) & 0xFFFF]
            elif op in ("if-eq", "if-ne"): w = [(a[1] << 12) | (a[0] << 8) | (0x32 if op == "if-eq" else 0x33), (labels[a[2]] - pc) & 0xFFFF]
            elif op in INVOKE:
                regs, ref = a[0], a[1]
                assert len(regs) <= 5 and all(r < 16 for r in regs)
                exp = words(ref[3]) + (0 if op == "invoke-static" else 1)
                assert len(regs) == exp, (m["name"], op, ref, regs)
                r = list(regs) + [0] * (5 - len(regs))
                w = [(len(regs) << 12) | (r[4] << 8) | INVOKE[op], midx[ref], (r[3] << 12) | (r[2] << 8) | (r[1] << 4) | r[0]]
                outs = max(outs, len(regs))
            else: raise ValueError(op)
            assert len(w) == SIZE[op]; out += w; pc += len(w)
        ins_n = words(m["params"]) + (0 if m.get("static") else 1)
        tries = [(labels[s], labels[e] - labels[s], labels[h]) for s, e, h in m.get("tries", [])]
        return out, ins_n, outs, tries

    off = 0x70
    str_ids_off = off; off += 4 * len(S)
    type_ids_off = off; off += 4 * len(TY)
    proto_ids_off = off; off += 12 * len(PR)
    field_ids_off = off; off += 8 * len(FL)
    meth_ids_off = off; off += 8 * len(ME)
    class_defs_off = off; off += 32 * len(classes)
    data_off = off
    data = bytearray()
    def at(): return data_off + len(data)
    def align4():
        while at() % 4: data.append(0)
    code_offs, n_code, first_code = {}, 0, None
    for cl in classes:
        for m in cl["methods"]:
            insns, ins_n, outs, tries = assemble(m, cl)
            align4(); o = at(); first_code = first_code or o; code_offs[(cl["name"], m["name"])] = o; n_code += 1
            item = u16(m["regs"]) + u16(ins_n) + u16(outs) + u16(len(tries)) + u32(0) + u32(len(insns)) + b"".join(u16(x) for x in insns)
            if tries:
                if len(insns) % 2: item += u16(0)
                hl = uleb(len(tries)); hoffs = []
                for _, _, h in tries: hoffs.append(len(hl)); hl += sleb(0) + uleb(h)        # nur catch-all
                for (s, cnt, _), ho in zip(tries, hoffs): item += u32(s) + u16(cnt) + u16(ho)
                item += hl
            assert m["regs"] >= ins_n
            data += item
    tl_offs, first_tl = {}, None
    lists = [p[1] for p in PR if p[1]] + [tuple(cl.get("interfaces", [])) for cl in classes if cl.get("interfaces")]
    for lst in lists:
        if lst in tl_offs: continue
        align4(); tl_offs[lst] = at(); first_tl = first_tl or tl_offs[lst]
        data += u32(len(lst)) + b"".join(u16(tidx[t]) for t in lst)
    sd_first, sd_offs = at(), []
    for s in S:
        sd_offs.append(at()); data += uleb(len(s)) + s.encode("utf-8") + b"\0"
    cd_offs, cd_first = [], at()
    for cl in classes:
        cd_offs.append(at())
        cf = sorted([(fidx[(cl["name"], n, t)], acc) for n, t, acc in cl.get("fields", [])])
        direct = sorted([(midx[(cl["name"], m["name"], m["ret"], tuple(m["params"]))], m["acc"], code_offs[(cl["name"], m["name"])])
                         for m in cl["methods"] if m.get("static") or m["name"] == "<init>"])
        virt = sorted([(midx[(cl["name"], m["name"], m["ret"], tuple(m["params"]))], m["acc"], code_offs[(cl["name"], m["name"])])
                       for m in cl["methods"] if not (m.get("static") or m["name"] == "<init>")])
        data += uleb(0) + uleb(len(cf)) + uleb(len(direct)) + uleb(len(virt))
        prev = 0
        for i, (fi, acc) in enumerate(cf): data += uleb(fi - (prev if i else 0)) + uleb(acc); prev = fi
        for group in (direct, virt):
            prev = 0
            for i, (mi, acc, co) in enumerate(group): data += uleb(mi - (prev if i else 0)) + uleb(acc) + uleb(co); prev = mi
    align4(); map_off = at()
    items = [(0x0000, 1, 0), (0x0001, len(S), str_ids_off), (0x0002, len(TY), type_ids_off), (0x0003, len(PR), proto_ids_off),
             (0x0004, len(FL), field_ids_off), (0x0005, len(ME), meth_ids_off), (0x0006, len(classes), class_defs_off),
             (0x2001, n_code, first_code), (0x1001, len(tl_offs), first_tl or 0), (0x2002, len(S), sd_first),
             (0x2000, len(classes), cd_first), (0x1000, 1, map_off)]
    items = sorted([i for i in items if i[1]], key=lambda i: i[2])
    data += u32(len(items)) + b"".join(u16(t) + u16(0) + u32(n) + u32(o) for t, n, o in items)

    body = bytearray()
    body += b"".join(u32(o) for o in sd_offs)
    body += b"".join(u32(sidx[t]) for t in TY)
    for r, ps in PR: body += u32(sidx[shorty(r, ps)]) + u32(tidx[r]) + u32(tl_offs[ps] if ps else 0)
    for c, n, t in FL: body += u16(tidx[c]) + u16(tidx[t]) + u32(sidx[n])
    for c, n, r, ps in ME: body += u16(tidx[c]) + u16(pidx[(r, ps)]) + u32(sidx[n])
    for cl, cdo in zip(classes, cd_offs):
        itf = tuple(cl.get("interfaces", []))
        body += u32(tidx[cl["name"]]) + u32(cl.get("acc", 1)) + u32(tidx[cl["super"]]) + u32(tl_offs[itf] if itf else 0) \
              + u32(0xFFFFFFFF) + u32(0) + u32(cdo) + u32(0)
    assert 0x70 + len(body) == data_off
    size = data_off + len(data)
    hdr = (b"dex\n035\0" + u32(0) + b"\0" * 20 + u32(size) + u32(0x70) + u32(0x12345678) + u32(0) + u32(0) + u32(map_off)
           + u32(len(S)) + u32(str_ids_off) + u32(len(TY)) + u32(type_ids_off) + u32(len(PR)) + u32(proto_ids_off)
           + u32(len(FL)) + u32(field_ids_off if FL else 0) + u32(len(ME)) + u32(meth_ids_off)
           + u32(len(classes)) + u32(class_defs_off) + u32(len(data)) + u32(data_off))
    dex = bytearray(hdr + body + data)
    dex[12:32] = hashlib.sha1(dex[32:]).digest()
    dex[8:12] = u32(zlib.adler32(bytes(dex[12:])))
    return bytes(dex)
