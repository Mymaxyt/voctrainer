"""Erzeugt tests/fsrs_cases.json mit dem offiziellen py-fsrs (Referenz für tests/engine.test.js).
Aufruf: python3 tests/make_fsrs_cases.py <Ordner, der das Paket fsrs enthält> tests/fsrs_cases.json
"""
import sys, json, random
sys.path.insert(0, sys.argv[1])
from datetime import datetime, timedelta, timezone
from fsrs import Scheduler, Card, Rating
random.seed(7)
sched = Scheduler(enable_fuzzing=False)
cases = []
for c in range(300):
    t = datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc)
    card = Card(); seq = []
    for k in range(random.randint(1, 12)):
        gap = random.choice([0.5, 2, 9, 30, 70, 300, 900, 1500, 2000, 3000, 6000, 14000]) * 60
        t = t + timedelta(seconds=gap)
        r = random.choice([1, 2, 3, 3, 3])
        card, _ = sched.review_card(card, Rating(r), t)
        seq.append([int(t.timestamp() * 1000), r, round(card.stability, 10), round(card.difficulty, 10)])
    cases.append(seq)
json.dump(cases, open(sys.argv[2], "w"))
print("cases", len(cases))
