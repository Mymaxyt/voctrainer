/* Lernmodell des Vokabeltrainers (ab Version 1.15)
   Reine Rechenlogik ohne Bildschirm: build.py setzt diese Datei in die App ein, tests/engine.test.js prüft sie mit Node.

   Verlauf je Wort:  hist[wortKey] = [[zeit, note, modus, fehlerart, partner], …]   (fehlerart/partner nur bei Fehlern)
     note       1 = falsch · 2 = richtig mit Hilfe (Tipp, Anfangsbuchstaben, Karte selbst bewertet) · 3 = richtig ohne Hilfe getippt
     modus      w = Schreiben (Deutsch → Englisch) · c = Lückensatz · t = Lückentext · x = Prüfungssatz · k = Karteikarte · l = vor 1.15
     fehlerart  s = Rechtschreibung · f = Form · v = Verwechslung · w = falsches Wort · n = nicht gewusst
   Ein "Wort" ist alles, was gleich geschrieben wird: market share aus Kapitel 3 und 7 teilen sich einen Verlauf.

   Gedächtnismodell: FSRS-6 mit den offiziellen Standardparametern (py-fsrs 6, scheduler.py).
   Daraus kommt die Wahrscheinlichkeit, ein Wort zu einem Zeitpunkt noch abrufen zu können (Prognose für den Prüfungstag).
   Die Lernstufen dagegen sind reine Fakten aus dem Verlauf (wie oft, an wie vielen Tagen, ob im Satzzusammenhang). */
const Engine = (() => {
"use strict";
const MIN = 60e3, HOUR = 60 * MIN, DAY = 24 * HOUR, DAY_START_H = 4;   // ein Lerntag geht von 04:00 bis 04:00

// ---------- FSRS-6
const P = [0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001, 1.8722, 0.1666, 0.796,
           1.4835, 0.0614, 0.2629, 1.6483, 0.6014, 1.8729, 0.5425, 0.0912, 0.0658, 0.1542];
const DECAY = -P[20], FACTOR = Math.pow(0.9, 1 / DECAY) - 1, S_MIN = 0.001;
const clampD = d => Math.min(10, Math.max(1, d));
const clampS = s => Math.max(S_MIN, s);
const initS = r => clampS(P[r - 1]);
const initD = (r, clamp = true) => { const d = P[4] - Math.exp(P[5] * (r - 1)) + 1; return clamp ? clampD(d) : d; };
const retr = (S, days) => Math.pow(1 + FACTOR * Math.max(0, days) / S, DECAY);
function shortS(S, r){
  let inc = Math.exp(P[17] * (r - 3 + P[18])) * Math.pow(S, -P[19]);
  if(r >= 2) inc = Math.max(inc, 1);
  return clampS(S * inc);
}
function nextD(D, r){
  const d2 = D + (10 - D) * (-P[6] * (r - 3)) / 9;
  return clampD(P[7] * initD(4, false) + (1 - P[7]) * d2);
}
function recallS(D, S, R, r){
  return S * (1 + Math.exp(P[8]) * (11 - D) * Math.pow(S, -P[9]) * (Math.exp((1 - R) * P[10]) - 1) * (r === 2 ? P[15] : 1) * (r === 4 ? P[16] : 1));
}
function forgetS(D, S, R){
  const longTerm = P[11] * Math.pow(D, -P[12]) * (Math.pow(S + 1, P[13]) - 1) * Math.exp((1 - R) * P[14]);
  return Math.min(longTerm, S / Math.exp(P[17] * P[18]));
}
// Verlauf (zeitlich sortiert) → Stabilität S (Tage), Schwierigkeit D (1–10), letzte Abfrage
function memory(atts){
  let S = null, D = null, last = 0;
  for(const a of atts){
    const r = a[1];
    if(S === null){ S = initS(r); D = initD(r); }
    else {
      const el = (a[0] - last) / DAY;
      if(el < 1) S = shortS(S, r);
      else { const R = retr(S, Math.floor(el)); S = clampS(r === 1 ? forgetS(D, S, R) : recallS(D, S, R, r)); }
      D = nextD(D, r);
    }
    last = a[0];
  }
  return S === null ? null : {S, D, last};
}
const recall = (m, t) => m ? retr(m.S, (t - m.last) / DAY) : 0;

// ---------- Tage
function dayStart(t){ const d = new Date(t); if(d.getHours() < DAY_START_H) d.setDate(d.getDate() - 1); d.setHours(DAY_START_H, 0, 0, 0); return d.getTime(); }
function dayKey(t){ const d = new Date(dayStart(t)); return d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate(); }

// ---------- Text: tolerant bei Groß/Klein, Leerzeichen, Bindestrichen, Satzzeichen und a/an/the/to am Anfang
const norm = s => String(s == null ? "" : s).toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "")
  .replace(/^\s*(a|an|the|to)\s+/, "").replace(/[\s\-‐-―\/.,;:'’`"()…]/g, "");
function accepted(v){
  const out = new Set();
  for(const t of [v.e, ...(v.a || []), ...(v.g ? [v.g] : [])]){ out.add(norm(t)); out.add(norm(t.replace(/\([^)]*\)/g, " "))); }
  out.delete(""); return out;
}
// Schreibweisen für die Anzeige und den Buchstabenvergleich
function forms(v){
  const out = [], add = s => { s = String(s || "").replace(/\s+/g, " ").trim(); if(s && !out.includes(s)) out.push(s); };
  add(v.e.replace(/\s*\([^)]*\)\s*/g, " ")); add(v.g); for(const a of v.a || []) add(a); add(v.e);
  return out;
}

// ---------- Wörter
let DATA = [], UNITS = [], UNIT = new Map(), ENTRY_UNIT = [], ACC = new Map();
function init(data){
  DATA = data; UNITS = []; UNIT = new Map(); ENTRY_UNIT = []; ACC = new Map();
  data.forEach((v, i) => {
    const k = norm(v.e);
    let u = UNIT.get(k);
    if(!u){ u = {k, idx: UNITS.length, entries: [], acc: new Set(), forms: [], chaps: [], syn: [], sents: []}; UNIT.set(k, u); UNITS.push(u); }
    u.entries.push(i); ENTRY_UNIT[i] = u;
    for(const a of accepted(v)) u.acc.add(a);
    for(const f of forms(v)) if(!u.forms.includes(f)) u.forms.push(f);
    const ch = v.c.split(" ")[0]; if(!u.chaps.includes(ch)) u.chaps.push(ch);
    for(const y of String(v.y || "").split(",").map(s => s.trim()).filter(Boolean)) if(!u.syn.includes(y)) u.syn.push(y);
    for(const s of v.t || []) u.sents.push({s: Array.isArray(s) ? s[0] : s, g: Array.isArray(s) ? s[1] : v.g, i});
  });
  for(const u of UNITS) for(const a of u.acc) if(!ACC.has(a)) ACC.set(a, u);
  return UNITS;
}
const unitOf = i => ENTRY_UNIT[i];
const unitByKey = k => UNIT.get(k);
const isRight = (u, typed, extra) => { const t = norm(typed); return t !== "" && (u.acc.has(t) || (!!extra && norm(extra) === t)); };

// ---------- Fehlerarten
function dist(a, b){                       // Damerau-Levenshtein (Vertauschung zweier Nachbarbuchstaben = 1 Fehler)
  const m = a.length, n = b.length;
  if(!m) return n; if(!n) return m;
  let p2 = null, p1 = Array.from({length: n + 1}, (_, j) => j);
  for(let i = 1; i <= m; i++){
    const c = [i];
    for(let j = 1; j <= n; j++){
      let v = Math.min(p1[j] + 1, c[j - 1] + 1, p1[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      if(i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) v = Math.min(v, p2[j - 2] + 1);
      c[j] = v;
    }
    p2 = p1; p1 = c;
  }
  return p1[n];
}
const tol = n => n <= 4 ? 1 : n <= 9 ? 2 : 3;
const toks = s => String(s || "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/\([^)]*\)/g, " ")
  .split(/[\s\-‐-―\/]+/).map(w => w.replace(/[^a-z0-9&]/g, "")).filter(Boolean);
const FUNC = new Set(["a", "an", "the", "of", "to", "in", "from", "for", "and", "on", "at", "by"]);
const SUFF = ["s", "es", "ies", "ed", "d", "ing", "al", "er", "ers", "or", "ors", "ion", "ions", "ation", "ations", "ment", "ments", "n", "en", "ly", "ity", "ive", "ness"];
function stem(w){
  if(w.length > 4 && w.endsWith("ies")) return w.slice(0, -3) + "y";
  if(/(ss|us|is)$/.test(w)) return w;
  if(w.length > 4 && /(ch|sh|x|z)es$/.test(w)) return w.slice(0, -2);
  if(w.length > 3 && w.endsWith("s")) return w.slice(0, -1);
  return w;
}
function related(a, b){
  if(a === b || stem(a) === stem(b)) return true;
  const [s, l] = a.length <= b.length ? [a, b] : [b, a];
  for(const base of new Set([s, s.replace(/e$/, ""), s.replace(/y$/, "i")]))
    if(base.length >= 3 && l.startsWith(base) && SUFF.includes(l.slice(base.length))) return true;
  return false;
}
// Gleiche Wörter, aber andere Endung / Reihenfolge / kleine Wörter → Beschreibung, sonst null
function formDiff(typed, form){
  const A = toks(typed), B = toks(form);
  if(!A.length || !B.length || A.join(" ") === B.join(" ")) return null;
  if(A.length === B.length && [...A].sort().join() === [...B].sort().join()) return "Wortstellung";
  const ca = A.filter(w => !FUNC.has(w)), cb = B.filter(w => !FUNC.has(w));
  if(ca.length && ca.join(" ") === cb.join(" ")) return "kleine Wörter (the, of, a …)";
  if(ca.length > 1 && [...ca].sort().join() === [...cb].sort().join()) return "Wortstellung";
  if(!ca.length || ca.length !== cb.length) return null;
  const pairs = [];
  for(let i = 0; i < ca.length; i++) if(ca[i] !== cb[i]){ if(!related(ca[i], cb[i])) return null; pairs.push(`„${ca[i]}“ statt „${cb[i]}“`); }
  return pairs.length && pairs.length <= 2 ? "Endung: " + pairs.join(", ") : null;
}
function closest(u, typed){                // Schreibweise des Worts, die der Eingabe am nächsten ist
  const t = norm(typed); let best = u.forms[0], bd = Infinity;
  for(const f of u.forms){ const d = dist(t, norm(f)); if(d < bd){ bd = d; best = f; } }
  return {form: best, d: bd};
}
function spellingOnly(typed, form){        // nur Tippfehler: Wort für Wort innerhalb der Toleranz
  let A = toks(typed), B = toks(form);
  if(A.length !== B.length){ A = A.filter(w => !FUNC.has(w)); B = B.filter(w => !FUNC.has(w)); }
  if(A.length === B.length && A.length > 1){
    let any = false;
    for(let i = 0; i < A.length; i++) if(A[i] !== B[i]){ if(dist(A[i], B[i]) > tol(B[i].length)) return false; any = true; }
    return any;
  }
  const a = norm(typed), b = norm(form), d = dist(a, b);
  return d > 0 && d <= tol(b.length);
}
// → {e: null} richtig · {e: "s"|"f"|"v"|"w"|"n", p: partnerKey?, d: detail?}
function classify(u, typed){
  const t = norm(typed);
  if(!t) return {e: "n"};
  if(u.acc.has(t)) return {e: null};
  let fd = null; for(const f of u.forms){ fd = formDiff(typed, f); if(fd) break; }
  const ex = ACC.get(t);
  if(ex && ex !== u) return fd ? {e: "f", p: ex.k, d: fd} : {e: "v", p: ex.k};
  if(fd) return {e: "f", d: fd};
  const own = new Set(u.forms.flatMap(toks));
  for(const w of toks(typed)){
    if(own.has(w) || FUNC.has(w)) continue;
    const o = ACC.get(w) || ACC.get(stem(w)); if(o && o !== u) return {e: "v", p: o.k};
  }
  // abgebrochen oder nur ein Teil (Anfang bzw. Ende des Ausdrucks)
  const short = Math.min(...[...u.acc].map(a => a.length));
  if(t.length <= 3 && short >= 6) return {e: "n", d: "unvollständig"};
  for(const a of u.acc) if(t.length < a.length - 2 && (a.endsWith(t) || dist(t, a.slice(0, t.length)) <= (t.length >= 6 ? 1 : 0))) return {e: "n", d: "unvollständig"};
  const c = closest(u, typed);
  if(spellingOnly(typed, c.form)) return {e: "s"};
  let bo = null, bd = Infinity;
  for(const o of UNITS){ if(o === u) continue; for(const a of o.acc){ const d = dist(t, a); if(d < bd){ bd = d; bo = o; } } }
  if(bo && bd <= tol(t.length) && bd < c.d) return {e: "v", p: bo.k};
  return {e: "w"};
}
const ERR = {s: "Rechtschreibung", f: "Form", v: "Verwechslung", w: "Falsches Wort", n: "Nicht gewusst"};
// Buchstabenvergleich für die Anzeige: [[op, getippt, richtig]] mit op = "=" gleich, "~" falsch, "+" zu viel, "-" fehlt
function align(typed, target){
  const a = String(typed), b = String(target), A = a.toLowerCase(), B = b.toLowerCase(), m = a.length, n = b.length;
  const D = []; for(let i = 0; i <= m; i++){ D.push(new Array(n + 1).fill(0)); D[i][0] = i; } for(let j = 0; j <= n; j++) D[0][j] = j;
  for(let i = 1; i <= m; i++) for(let j = 1; j <= n; j++) D[i][j] = Math.min(D[i - 1][j] + 1, D[i][j - 1] + 1, D[i - 1][j - 1] + (A[i - 1] === B[j - 1] ? 0 : 1));
  const ops = []; let i = m, j = n;
  while(i > 0 || j > 0){
    if(i > 0 && j > 0 && D[i][j] === D[i - 1][j - 1] + (A[i - 1] === B[j - 1] ? 0 : 1)){ ops.push([A[i - 1] === B[j - 1] ? "=" : "~", a[i - 1], b[j - 1]]); i--; j--; }
    else if(i > 0 && D[i][j] === D[i - 1][j] + 1){ ops.push(["+", a[i - 1], ""]); i--; }
    else { ops.push(["-", "", b[j - 1]]); j--; }
  }
  return ops.reverse();
}

// ---------- Lernstufen (Fakten aus dem Verlauf)
const TYPED = "wctxl", CTX = "ctx";
const isTyped = a => TYPED.includes(a[2]);
const okTyped = a => a[1] === 3 && isTyped(a);
const lapse = a => a[1] === 1 || (a[1] === 2 && isTyped(a));     // falsch oder nur mit Tipp
const STAGES = ["Neu", "In Arbeit", "Gefestigt", "Sicher", "Prüfungsfest"];
// 0 Neu · 1 In Arbeit · 2 Gefestigt: seit dem letzten Fehler 2× ohne Hilfe richtig getippt, ≥ 10 Min. auseinander
// 3 Sicher: dazu an ≥ 2 Tagen und ≥ 1× im Satz · 4 Prüfungsfest: ≥ 3× an ≥ 3 Tagen, davon ≥ 2× im Satz
function stage(atts){
  if(!atts || !atts.length) return 0;
  let li = -1; for(let i = atts.length - 1; i >= 0; i--) if(lapse(atts[i])){ li = i; break; }
  const ok = atts.slice(li + 1).filter(okTyped);
  if(ok.length < 2 || ok[ok.length - 1][0] - ok[0][0] < 10 * MIN) return 1;
  const days = new Set(ok.map(a => dayKey(a[0]))).size, ctx = ok.filter(a => CTX.includes(a[2])).length;
  if(ok.length >= 3 && days >= 3 && ctx >= 2) return 4;
  if(days >= 2 && ctx >= 1) return 3;
  return 2;
}
// Heute: geschafft = einmal ohne Hilfe richtig; nach einem Fehler zweimal (nach ~1 und ~10 Min. erneut)
function today(atts, now){
  const d0 = dayStart(now), T = (atts || []).filter(a => a[0] >= d0);
  let li = -1, err = false;
  for(let i = T.length - 1; i >= 0; i--) if(lapse(T[i])){ li = i; err = T[i][1] === 1; break; }
  const ok = T.slice(li + 1).filter(okTyped).length, need = err ? 2 : 1, tried = T.some(isTyped);
  if(ok >= need) return {done: true, tried, learning: false};
  if(err) return {done: false, tried, learning: true, step: ok + 1, due: T[T.length - 1][0] + (ok ? 10 * MIN : MIN)};
  return {done: false, tried, learning: false};
}
function info(atts, now, examAt){
  atts = atts || [];
  const m = memory(atts), at = examAt && examAt > now ? examAt : now;
  return {n: atts.length, stage: stage(atts), mem: m, rNow: recall(m, now), rExam: recall(m, at), today: today(atts, now),
          errs: atts.filter(a => a[1] === 1).length, last: atts.length ? atts[atts.length - 1] : null};
}

// ---------- Was kommt als Nächstes? (Lernplan)
function hash(s){ let h = 2166136261; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0) / 4294967296; }
// pool: Wörter · infos: Map key → info · recent: zuletzt abgefragte Keys · bonus: nach dem Tagesziel weiterüben
function pick(pool, infos, now, recent, opt){
  opt = opt || {};
  const before = !opt.examAt || now < opt.examAt, seed = opt.seed || "";
  const last = recent[recent.length - 1], r3 = new Set(recent.slice(-3));
  const I = u => infos.get(u.k), jit = u => (hash(u.k + seed) - 0.5) * 0.1;
  const learn = pool.filter(u => I(u).today.learning);
  const due = learn.filter(u => I(u).today.due <= now).sort((a, b) => I(a).today.due - I(b).today.due);
  const open = pool.filter(u => { const i = I(u); return !i.today.done && !i.today.learning && (before || i.rNow < 0.9); })
    .sort((a, b) => (I(a).rNow + jit(a)) - (I(b).rNow + jit(b)));
  // Wiederholungen frühestens nach drei anderen Wörtern – es sei denn, die letzte Antwort ist schon 2 Min. her
  const fresh = new Set([...r3].filter(k => { const i = infos.get(k); return i && i.last && now - i.last[0] < 2 * MIN; }));
  const tries = [[due, fresh, "learn"], [open, r3, "open"], [due, new Set([last]), "learn"], [open, new Set([last]), "open"], [due, new Set(), "learn"], [open, new Set(), "open"]];
  for(const [list, skip, kind] of tries){
    const u = list.find(x => !skip.has(x.k));
    if(u) return {u, kind, step: kind === "learn" ? I(u).today.step : 0};
  }
  const wait = learn.length ? Math.max(0, Math.min(...learn.map(u => I(u).today.due)) - now) : null;
  if(opt.bonus){
    const cand = pool.filter(u => I(u).n && !r3.has(u.k) && (!I(u).last || now - I(u).last[0] > 10 * MIN))
      .sort((a, b) => (I(a).rExam + jit(a)) - (I(b).rExam + jit(b)));
    const u = cand[0] || pool.filter(x => x.k !== last).sort((a, b) => I(a).rExam - I(b).rExam)[0];
    if(u) return {u, kind: "bonus", step: 0, wait, learning: learn.length};
  }
  return {u: null, wait, learning: learn.length};
}
// Abfrageart im Lernplan: neue Wörter erst Deutsch → Englisch, sonst Lückensatz (wie in der Prüfung);
// nach einem Fehler erst über die Bedeutung, dann im anderen Satz
function modeFor(u, atts, kind, step){
  if(!u.sents.length) return "w";
  if(kind === "learn") return step === 1 ? "w" : "c";
  return (atts || []).some(a => a[1] === 3 && (a[2] === "w" || a[2] === "l")) ? "c" : "w";
}
const sentence = (u, atts) => u.sents[(atts || []).filter(a => a[2] === "c").length % u.sents.length];
const promptEntry = (u, atts) => u.entries[(atts || []).filter(a => a[2] === "w").length % u.entries.length];

// ---------- Prognose
function mulberry(a){ return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
// Wahrscheinlichkeit, in einer Prüfung mit n zufälligen Wörtern mindestens den Anteil need zu schaffen
function chance(rs, n, need, sims){
  n = Math.min(n || 30, rs.length); sims = sims || 4000; if(!n) return 0;
  const rnd = mulberry(20261126), idx = rs.map((_, i) => i), goal = Math.ceil(need * n - 1e-9);
  let hit = 0;
  for(let s = 0; s < sims; s++){
    let ok = 0;
    for(let i = 0; i < n; i++){ const j = i + Math.floor(rnd() * (idx.length - i)); const x = idx[i]; idx[i] = idx[j]; idx[j] = x; if(rnd() < rs[idx[i]]) ok++; }
    if(ok >= goal) hit++;
  }
  return hit / sims;
}
function note(pct){                       // übliche Notenskala, nur Richtwert
  for(const [p, n] of [[95, "1,0"], [90, "1,3"], [85, "1,7"], [80, "2,0"], [75, "2,3"], [70, "2,7"], [65, "3,0"], [60, "3,3"], [55, "3,7"], [50, "4,0"]]) if(pct >= p) return n;
  return "5,0";
}

// ---------- Übernahme aus Version ≤ 1.14 (Kästchen-System + Fehlerprotokoll)
// Fehler kommen mit Zeit und Antwort aus dem Protokoll ("Zählt doch" zählt als Fehler);
// richtige Antworten sind nur als Zähler gespeichert – vorsichtig übernommen: höchstens eine, zum Zeitpunkt der letzten Antwort.
function migrate(srs, log, logCleared, now){
  srs = srs || {}; const hist = {}, byEntry = new Map(), logBy = new Map();
  DATA.forEach((v, i) => byEntry.set(v.n + "|" + v.e, i));
  for(const e of log || []){
    if(e.t <= (logCleared || 0)) continue;
    const i = byEntry.get(e.n + "|" + e.e); if(i == null) continue;
    if(!logBy.has(i)) logBy.set(i, []); logBy.get(i).push(e);
  }
  const add = (u, a) => (hist[u.k] || (hist[u.k] = [])).push(a);
  const idx = new Set([...logBy.keys()]); for(const k of Object.keys(srs)){ const i = byEntry.get(k); if(i != null) idx.add(i); }
  for(const i of idx){
    const v = DATA[i], u = ENTRY_UNIT[i], r = srs[v.n + "|" + v.e] || {}, L = logBy.get(i) || [];
    for(const e of L){                      // Modus "l": stammt aus der Zeit vor 1.15 (zählt als getippt, nicht im Satz)
      const m = e.m === "Karte" ? "k" : "l";
      const c = m === "k" ? {e: "n"} : classify(u, e.a);
      if(c.e === null) continue;            // gilt inzwischen als richtig (z. B. "household products")
      const a = [e.t, 1, m, c.e]; if(c.p) a.push(c.p); add(u, a);
    }
    const u0 = r.u || (r.due && r.r ? r.due - HOUR : 0);
    const times = L.map(e => e.t), first = Math.min(u0 || now, ...times);
    const unlogged = Math.min(5, Math.max(0, (r.w || 0) - L.filter(e => !e.ov).length));
    for(let k = unlogged; k >= 1; k--) add(u, [first - k * MIN, 1, "l", "n"]);
    if(u0){
      const right = (r.b || 0) > 0, nearErr = times.some(t => u0 - t >= 0 && u0 - t < 30e3);
      if(right && !nearErr) add(u, [u0, 3, "l"]);
      else if(!right && (r.w || 0) > 0 && !times.some(t => Math.abs(t - u0) < 30e3)) add(u, [u0, 1, "l", "n"]);
    }
  }
  for(const k of Object.keys(hist)) hist[k] = tidy(hist[k]);
  return hist;
}
// Sortieren, doppelte Zeitstempel entfernen und dieselbe alte Antwort aus zwei Quellen (Protokoll + Kästchen, < 2 s) zusammenfassen
function tidy(list){
  const m = new Map(); for(const a of list) if(Array.isArray(a) && Number.isFinite(a[0]) && !m.has(a[0])) m.set(a[0], a);
  const out = [];
  for(const a of [...m.values()].sort((x, y) => x[0] - y[0])){
    const p = out[out.length - 1];
    if(p && a[0] - p[0] < 2000 && a[1] === p[1] && (a[2] === "l" || p[2] === "l")){
      const info = x => (x[2] !== "l" ? 4 : 0) + (x[3] && x[3] !== "n" ? 2 : 0) + (x.length > 4 ? 1 : 0);
      const keep = info(a) > info(p) ? a : p;
      out[out.length - 1] = keep; continue;
    }
    out.push(a);
  }
  return out;
}

// ---------- Geräte-Sync: Verläufe vereinigen (jede Antwort ist ein Ereignis mit Zeitstempel)
function mergeHist(local, remote){
  local = local || {}; remote = remote || {};
  let pulled = false, push = false; const out = {};
  for(const k of new Set([...Object.keys(local), ...Object.keys(remote)])){
    const L = local[k] || [], R = remote[k] || [], lt = new Set(L.map(a => a[0])), rt = new Set(R.map(a => a[0]));
    if(R.some(a => !lt.has(a[0]))) pulled = true;
    if(L.some(a => !rt.has(a[0]))) push = true;
    out[k] = tidy([...L, ...R]);
  }
  return {hist: out, pulled, push};
}
// Für ältere App-Versionen auf dem anderen Gerät: Kästchen-Stand aus dem Verlauf (Format bis 1.14)
const OLD_IV = [0, 10 * MIN, HOUR, 6 * HOUR, DAY, 3 * DAY, 7 * DAY];
function legacySrs(hist){
  const out = {};
  DATA.forEach((v, i) => {
    const atts = hist[ENTRY_UNIT[i].k]; if(!atts || !atts.length) return;
    const st = stage(atts), last = atts[atts.length - 1], b = st >= 2 ? st : (last[1] >= 2 ? 1 : 0);
    out[v.n + "|" + v.e] = {b, w: atts.filter(a => a[1] === 1).length, r: atts.filter(a => a[1] >= 2).length, due: last[0] + OLD_IV[b], u: last[0]};
  });
  return out;
}
// Antworten, die ein Gerät mit alter Version gegeben hat, als Ereignis übernehmen
function absorbLegacy(hist, srs){
  let changed = false;
  DATA.forEach((v, i) => {
    const r = (srs || {})[v.n + "|" + v.e]; if(!r || !r.u) return;
    const k = ENTRY_UNIT[i].k, atts = hist[k] || [], lastT = atts.length ? atts[atts.length - 1][0] : 0;
    if(r.u > lastT + 1000){ hist[k] = tidy([...atts, (r.b || 0) > 0 ? [r.u, 3, "l"] : [r.u, 1, "l", "n"]]); changed = true; }
  });
  return changed;
}

// ---------- Auswertungen für den Fortschritt
function errorsByType(hist, since){
  const c = {s: 0, f: 0, v: 0, w: 0, n: 0};
  for(const atts of Object.values(hist)) for(const a of atts) if(a[1] === 1 && a[0] >= since && a[2] !== "k") c[a[3] in c ? a[3] : "n"]++;
  return c;
}
function confusions(hist){
  const m = new Map();
  for(const [k, atts] of Object.entries(hist)) for(const a of atts) if(a[1] === 1 && a[4] && (a[3] === "v" || a[3] === "f") && UNIT.has(a[4])){
    const pair = [k, a[4]].sort(), id = pair.join("|"), x = m.get(id) || {a: pair[0], b: pair[1], n: 0, last: 0};
    x.n++; x.last = Math.max(x.last, a[0]); m.set(id, x);
  }
  return [...m.values()].sort((x, y) => y.n - x.n || y.last - x.last);
}
function daily(hist, now, n){
  const days = new Map();
  for(const [k, atts] of Object.entries(hist)) for(const a of atts){
    if(!isTyped(a) || a[2] === "l") continue;
    const d = dayKey(a[0]); if(!days.has(d)) days.set(d, {d, t: dayStart(a[0]), answers: 0, right: 0, first: new Map()});
    const x = days.get(d); x.answers++; if(a[1] === 3) x.right++;
    if(!x.first.has(k)) x.first.set(k, a[1] === 3);
  }
  return [...days.values()].sort((a, b) => b.d - a.d).slice(0, n || 7).map(x => {
    const done = Object.keys(hist).filter(k => today(hist[k].filter(a => a[0] < x.t + DAY), x.t + DAY - 1).done).length;
    const f = [...x.first.values()];
    return {d: x.d, t: x.t, answers: x.answers, right: x.right, words: f.length, firstOk: f.filter(Boolean).length, done};
  });
}

return {MIN, HOUR, DAY, P, STAGES, ERR, init, norm, accepted, forms, unitOf, unitByKey, get units(){ return UNITS; },
        isRight, classify, closest, align, dist, memory, recall, retr, stage, today, info, pick, modeFor, sentence, promptEntry,
        chance, note, dayStart, dayKey, migrate, tidy, mergeHist, legacySrs, absorbLegacy, errorsByType, confusions, daily, isTyped, okTyped};
})();
if(typeof module !== "undefined") module.exports = Engine;
