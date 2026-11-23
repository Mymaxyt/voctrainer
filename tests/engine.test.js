// Tests für src/engine.js – Aufruf: TZ=Europe/Berlin node tests/engine.test.js
const assert = require("assert"), fs = require("fs"), path = require("path");
const Engine = require("../src/engine.js");
const DATA = JSON.parse(require("child_process").execFileSync("python3", ["-I", path.join(__dirname, "../build.py"), "--data"], {encoding: "utf8", maxBuffer: 1 << 24}));
const units = Engine.init(DATA);
const { MIN, HOUR, DAY } = Engine;
let n = 0;
const test = (name, fn) => { try { fn(); n++; } catch (e) { console.error("FEHLER:", name); throw e; } };
const U = e => Engine.unitOf(DATA.findIndex(v => v.e === e));
const T0 = new Date(2026, 10, 23, 10, 0).getTime();      // Mo 23.11.2026 10:00

test("Wörter: 151 verschiedene, keine Überschneidung der Schreibweisen", () => {
  assert.strictEqual(units.length, 151);
  const seen = new Map();
  for (const u of units) for (const a of u.acc) { assert.ok(!seen.has(a) || seen.get(a) === u, "doppelt: " + a); seen.set(a, u); }
  assert.strictEqual(U("market share").entries.length, 2);
  assert.strictEqual(U("end-user"), U("end user"));
});

test("FSRS-6 stimmt mit py-fsrs überein", () => {
  const cases = JSON.parse(fs.readFileSync(path.join(__dirname, "fsrs_cases.json"), "utf8"));
  let checked = 0;
  for (const seq of cases) {
    const atts = [];
    for (const [t, r, S, D] of seq) {
      atts.push([t, r, "w"]);
      const m = Engine.memory(atts);
      assert.ok(Math.abs(m.S - S) < 1e-6 * Math.max(1, S), `S ${m.S} != ${S}`);
      assert.ok(Math.abs(m.D - D) < 1e-6, `D ${m.D} != ${D}`);
      checked++;
    }
  }
  assert.ok(checked > 1000);
});

test("Abrufwahrscheinlichkeit: 90 % nach S Tagen", () => {
  assert.ok(Math.abs(Engine.retr(5, 5) - 0.9) < 1e-9);
  assert.strictEqual(Engine.recall(null, T0), 0);
});

test("Fehlerarten", () => {
  const c = (e, a) => Engine.classify(U(e), a);
  assert.strictEqual(c("apparel", "apperal").e, "s");
  assert.strictEqual(c("materials handling", "materials handeling").e, "s");
  assert.strictEqual(c("subsidiary", "subsidary").e, "s");
  assert.strictEqual(c("catalogue", "cataloge").e, "s");
  assert.strictEqual(c("quotas", "qouatas").e, "s");
  assert.deepStrictEqual(c("quotation", "qouatas"), { e: "v", p: "quotas" });
  assert.strictEqual(c("appliances", "appliance").e, "f");
  assert.strictEqual(c("materials handling", "material handling").e, "f");
  assert.strictEqual(c("reaches saturation", "reach saturation").e, "f");
  assert.strictEqual(c("gaps in the market", "market gaps").e, "f");
  assert.strictEqual(c("the activity of competitors", "the activity of the competitors").e, "f");
  const w = c("warehouses", "warehouse"); assert.strictEqual(w.e, "f"); assert.strictEqual(w.p, "warehouse");
  assert.deepStrictEqual(c("subsidiary", "subsidy"), { e: "v", p: "subsidy" });
  assert.deepStrictEqual(c("foreign subsidiary", "foreign subsidy"), { e: "v", p: "subsidy" });
  assert.deepStrictEqual(c("agent", "broker"), { e: "v", p: "broker" });
  assert.strictEqual(c("customer", "client").e, "v");
  assert.strictEqual(c("withdrawn from the market", "withdrawal").e, "v");
  assert.strictEqual(c("coordinate", "communicate").e, "w");
  assert.strictEqual(c("characteristic", "").e, "n");
  assert.strictEqual(c("materials handling", "materials").e, "n");
  assert.strictEqual(c("quotas", "qu").e, "n");
  assert.strictEqual(c("household (product)", "Household Products").e, null);   // Plural ist erlaubt
  assert.strictEqual(c("end-user", "end user").e, null);
  assert.strictEqual(c("Chief Operating Officer (COO)", "COO").e, null);
  assert.strictEqual(c("the activity of competitors", "activity of competitors").e, null);
});

test("Buchstabenvergleich", () => {
  const ops = Engine.align("handeling", "handling");
  assert.deepStrictEqual(ops.filter(o => o[0] !== "=").map(o => o[0] + o[1] + o[2]), ["+e"]);
  assert.strictEqual(Engine.align("Apperal", "apparel").filter(o => o[0] === "~").length, 2);
});

test("Lernstufen", () => {
  const st = a => Engine.stage(a);
  assert.strictEqual(st([]), 0);
  assert.strictEqual(st([[T0, 3, "w"]]), 1);
  assert.strictEqual(st([[T0, 3, "w"], [T0 + 5 * MIN, 3, "c"]]), 1);                       // zu dicht
  assert.strictEqual(st([[T0, 3, "w"], [T0 + 15 * MIN, 3, "w"]]), 2);
  assert.strictEqual(st([[T0, 3, "w"], [T0 + DAY, 3, "c"]]), 3);
  assert.strictEqual(st([[T0, 3, "k"], [T0 + DAY, 2, "k"]]), 1);                           // Karten zählen nicht
  const good = [[T0, 3, "c"], [T0 + DAY, 3, "w"], [T0 + 2 * DAY, 3, "c"]];
  assert.strictEqual(st(good), 4);
  assert.strictEqual(st([...good, [T0 + 2 * DAY + HOUR, 1, "c", "s"]]), 1);                 // Fehler setzt zurück
  assert.strictEqual(st([...good, [T0 + 2 * DAY + HOUR, 2, "w"]]), 1);                      // Tipp ebenso
  assert.strictEqual(st([[T0, 1, "w", "s"], ...good.map(a => [a[0] + HOUR, a[1], a[2]])]), 4);
});

test("Tagesziel und Lernschritte", () => {
  const td = (a, now) => Engine.today(a, now || T0 + HOUR);
  assert.deepStrictEqual(td([[T0, 3, "c"]]), { done: true, tried: true, learning: false });
  assert.strictEqual(td([[T0 - DAY, 3, "c"]]).done, false);
  let s = td([[T0, 1, "c", "s"]]);
  assert.ok(s.learning && s.step === 1 && s.due === T0 + MIN);
  s = td([[T0, 1, "c", "s"], [T0 + 2 * MIN, 3, "w"]]);
  assert.ok(s.learning && s.step === 2 && s.due === T0 + 12 * MIN);
  assert.strictEqual(td([[T0, 1, "c", "s"], [T0 + 2 * MIN, 3, "w"], [T0 + 13 * MIN, 3, "c"]]).done, true);
  assert.strictEqual(td([[T0, 2, "c"]]).done, false);
  // Lerntag beginnt um 4 Uhr
  const night = new Date(2026, 10, 24, 3, 30).getTime();
  assert.strictEqual(Engine.dayKey(night), 20261123);
  assert.strictEqual(Engine.dayKey(new Date(2026, 10, 24, 4, 0).getTime()), 20261124);
  assert.strictEqual(td([[T0, 3, "c"]], night).done, true);
});

test("Lernplan: fällige Wiederholung zuerst, sonst schwächstes offenes Wort", () => {
  const a = U("apparel"), b = U("freight"), c = U("debt");
  const hist = { [a.k]: [[T0 - 90e3, 1, "c", "s"]], [b.k]: [[T0 - DAY, 3, "c"]], [c.k]: [[T0 - 5 * DAY, 3, "c"]] };
  const infos = new Map(units.map(u => [u.k, Engine.info(hist[u.k], T0)]));
  const pool = [a, b, c];
  let p = Engine.pick(pool, infos, T0, [], {});
  assert.strictEqual(p.u, a); assert.strictEqual(p.kind, "learn"); assert.strictEqual(p.step, 1);
  p = Engine.pick(pool, infos, T0, [a.k], {});
  assert.strictEqual(p.u, c);                                         // gerade erst gefragt → erst andere; debt länger her → schwächer
  assert.strictEqual(Engine.pick(pool, infos, T0 + MIN, [a.k], {}).u, a);   // nach 2 Min. darf es wieder kommen
  p = Engine.pick([a], infos, T0 - 60e3, [], {});
  assert.strictEqual(p.u, null); assert.strictEqual(p.wait, 30e3);     // Lernschritt noch nicht fällig
  assert.strictEqual(Engine.pick([a], infos, T0 - 60e3, [], { bonus: true }).kind, "bonus");
  assert.strictEqual(Engine.modeFor(a, hist[a.k], "learn", 1), "w");
  assert.strictEqual(Engine.modeFor(c, hist[c.k], "open", 0), "w");                    // noch nie ohne Satz gewusst
  assert.strictEqual(Engine.modeFor(c, [[T0 - DAY, 3, "w"]], "open", 0), "c");
  assert.strictEqual(Engine.modeFor(c, [[T0 - DAY, 3, "l"]], "open", 0), "c");
  assert.strictEqual(Engine.modeFor(a, hist[a.k], "learn", 2), "c");
  assert.strictEqual(Engine.sentence(c, []).s, DATA[c.entries[0]].t[0]);
  assert.strictEqual(Engine.sentence(c, [[1, 3, "c"]]).s, DATA[c.entries[0]].t[1]);
  assert.strictEqual(Engine.modeFor(U("brokerage"), [], "open", 0), "w");
});

test("Prognose und Note", () => {
  assert.strictEqual(Engine.chance(new Array(151).fill(1), 30, 0.95), 1);
  assert.ok(Engine.chance(new Array(151).fill(0.5), 30, 0.95) < 0.01);
  const x = Engine.chance(new Array(151).fill(0.97), 30, 0.95);
  assert.ok(x > 0.7 && x < 0.85, x);                                  // P(≤ 1 Fehler) bei 30 Lücken ≈ 0,77
  assert.strictEqual(Engine.note(95), "1,0"); assert.strictEqual(Engine.note(94.9), "1,3"); assert.strictEqual(Engine.note(49), "5,0");
});

test("Übernahme aus 1.14", () => {
  const ap = DATA.find(v => v.e === "apparel"), mh = DATA.find(v => v.e === "materials handling"), fr = DATA.find(v => v.e === "freight");
  const srs = {
    [ap.n + "|" + ap.e]: { b: 2, w: 3, r: 4, due: T0, u: T0 - HOUR },
    [mh.n + "|" + mh.e]: { b: 1, w: 0, r: 2, due: T0, u: T0 - 2 * HOUR + 4000 },
    [fr.n + "|" + fr.e]: { b: 3, w: 0, r: 3, due: T0, u: T0 - DAY },
  };
  const log = [
    { id: "1", t: T0 - 3 * HOUR, m: "Schreiben", n: ap.n, e: ap.e, a: "apperal", ov: false },
    { id: "2", t: T0 - 2 * HOUR, m: "Schreiben", n: mh.n, e: mh.e, a: "material handling", ov: true },
    { id: "3", t: T0 - 9 * DAY, m: "Schreiben", n: ap.n, e: ap.e, a: "x", ov: false },
  ];
  const h = Engine.migrate(srs, log, T0 - 8 * DAY, T0);
  const A = h[U("apparel").k], M = h[U("materials handling").k], F = h[U("freight").k];
  assert.strictEqual(A.filter(a => a[1] === 1).length, 3);           // 1 protokolliert + 2 ohne Protokoll
  assert.deepStrictEqual(A[A.length - 1], [T0 - HOUR, 3, "l"]);
  assert.deepStrictEqual(M, [[T0 - 2 * HOUR, 1, "l", "f"]]);          // "Zählt doch" bleibt ein Fehler
  assert.deepStrictEqual(Engine.daily(h, T0), []);                   // alte Tage sind unvollständig → nicht im Verlauf
  assert.deepStrictEqual(F, [[T0 - DAY, 3, "l"]]);
  assert.strictEqual(Engine.stage(F), 1);
});

test("Sync: Verläufe vereinigen, ältere App-Versionen", () => {
  const k = U("apparel").k;
  const L = { [k]: [[1, 3, "w"], [3, 1, "c", "s"]] }, R = { [k]: [[2, 3, "c"], [3, 1, "c", "s"]], x: [[5, 3, "w"]] };
  const m = Engine.mergeHist(L, R);
  assert.deepStrictEqual(m.hist[k].map(a => a[0]), [1, 2, 3]);
  assert.ok(m.pulled && m.push);
  assert.deepStrictEqual(Engine.mergeHist(m.hist, m.hist), { hist: m.hist, pulled: false, push: false });
  // dieselbe alte Antwort von zwei Geräten (einmal aus dem Kästchen-Stand, einmal aus dem Protokoll übernommen)
  const dup = Engine.mergeHist({ [k]: [[T0, 1, "l", "n"]] }, { [k]: [[T0 + 3, 1, "l", "s"]] });
  assert.deepStrictEqual(dup.hist[k], [[T0 + 3, 1, "l", "s"]]);
  assert.strictEqual(Engine.tidy([[T0, 3, "x"], [T0 + 1, 3, "x"]]).length, 2);       // zwei echte Prüfungsantworten bleiben
  const hist = { [k]: [[T0, 3, "c"], [T0 + DAY, 3, "w"]] };
  const old = Engine.legacySrs(hist);
  const ap = DATA.find(v => v.e === "apparel");
  assert.strictEqual(old[ap.n + "|" + ap.e].u, T0 + DAY);
  assert.strictEqual(Engine.absorbLegacy(hist, old), false);           // eigener Stand ändert nichts
  old[ap.n + "|" + ap.e] = { b: 0, w: 1, r: 2, due: 0, u: T0 + 2 * DAY };
  assert.strictEqual(Engine.absorbLegacy(hist, old), true);
  assert.deepStrictEqual(hist[k][2], [T0 + 2 * DAY, 1, "l", "n"]);
});

test("Auswertungen", () => {
  const k1 = U("subsidiary").k, k2 = U("subsidy").k;
  const hist = { [k1]: [[T0, 1, "c", "v", k2], [T0 + MIN, 3, "w"]], [k2]: [[T0 + 2 * MIN, 1, "w", "v", k1], [T0 + 3 * MIN, 1, "w", "s"]] };
  assert.deepStrictEqual(Engine.errorsByType(hist, T0 - DAY), { s: 1, f: 0, v: 2, w: 0, n: 0 });
  const cf = Engine.confusions(hist);
  assert.strictEqual(cf.length, 1); assert.strictEqual(cf[0].n, 2);
  const d = Engine.daily(hist, T0 + HOUR);
  assert.strictEqual(d.length, 1); assert.strictEqual(d[0].answers, 4); assert.strictEqual(d[0].words, 2); assert.strictEqual(d[0].firstOk, 0);
});

console.log(`engine: ${n} Testgruppen bestanden`);
