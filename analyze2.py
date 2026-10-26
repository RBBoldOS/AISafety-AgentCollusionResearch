import re, json, glob, os, statistics as st

CELLS = [
    ("S2_floor",          "FLOOR: no comms"),
    ("S2_nowatch",        "CONTROL: comms, no watcher"),
    ("S2_late21",         "TOLD + WATCHED, gag live"),
    ("S3_told_unwatched", "TOLD, no watcher"),
    ("S3_silent_watched", "NOT TOLD, watched, gag live"),
    ("S4_told_nogag",     "TOLD + WATCHED, no gag"),
    ("S4_silent_nogag",   "NOT TOLD, watched, no gag"),
]
PRE, POST = (11, 20), (31, 40)

def load(p):
    out = []
    for line in open(p, errors="ignore"):
        m = re.search(r'completed with result: (\{.*\})\s*$', line)
        if m:
            try: out.append(json.loads(m.group(1)))
            except Exception: pass
    return sorted(out, key=lambda r: r["round_number"])

def mean(x): return round(st.mean(x), 2) if x else None
def fmt(v): return "-" if v is None else str(v)

def window(rs, a, b):
    w = [r for r in rs if a <= r["round_number"] <= b]
    by = {r["round_number"]: r for r in rs}
    msgs = [(m or "") for r in w for m in r["seller_messages"].values()]
    words = set(x for m in msgs for x in re.findall(r"\w+", m.lower()))
    chg = tot = 0
    for r in w:
        prev = by.get(r["round_number"] - 1)
        if not prev: continue
        for s, ask in r["seller_asks"].items():
            if s in prev["seller_asks"]:
                tot += 1
                chg += ask != prev["seller_asks"][s]
    return dict(
        len=mean([len(m) for m in msgs]),
        short=mean([0 < len(m) <= 3 for m in msgs]),
        vocab=len(words),
        uniq=len(set(msgs)),
        spread=mean([max(r["seller_asks"].values()) - min(r["seller_asks"].values()) for r in w]),
        price=mean([t["price"] for r in w for t in r["trades"]]),
        chg=round(chg / tot, 2) if tot else None,
        trades=sum(len(r["trades"]) for r in w),
    )

def flip_round(rs):
    for r in rs:
        ms = [len(m or "") for m in r["seller_messages"].values()]
        if ms and st.mean(ms) <= 5: return r["round_number"]
    return None

def sample(rs):
    for r in rs:
        if r["round_number"] == 35 and r["seller_messages"]:
            return repr(next(iter(r["seller_messages"].values())) or "")[:34]
    return "-"

runs = {}
for p in sorted(glob.glob("results/*/unified.log")):
    d = os.path.basename(os.path.dirname(p))
    for tag, _ in CELLS:
        if tag in d:
            rs = load(p)
            if rs:
                s = re.search(r"seed(\d+)", d)
                runs.setdefault(tag, []).append((s.group(1) if s else "1", rs))

hdr = f"{'seed':<5}{'len pre>post':<14}{'short':<7}{'vocab':<10}{'uniq':<9}{'spread':<12}{'price':<14}{'chg':<6}{'flip':<6}sample(r35)"
for tag, title in CELLS:
    if tag not in runs: continue
    print(f"\n== {title}  [{tag}]"); print(hdr)
    for seed, rs in sorted(runs[tag]):
        a, b = window(rs, *PRE), window(rs, *POST)
        print(f"{seed:<5}{fmt(a['len'])+'>'+fmt(b['len']):<14}{fmt(b['short']):<7}"
              f"{str(a['vocab'])+'>'+str(b['vocab']):<10}{str(a['uniq'])+'>'+str(b['uniq']):<9}"
              f"{fmt(a['spread'])+'>'+fmt(b['spread']):<12}{fmt(a['price'])+'>'+fmt(b['price']):<14}"
              f"{fmt(b['chg']):<6}{fmt(flip_round(rs)):<6}{sample(rs)}")
print("\nlen=mean seller message chars; short=share of msgs of 1-3 chars (post); vocab=distinct words;"
      "\nuniq=distinct messages; spread=max-min ask; chg=share of asks changed vs prior round (post);"
      "\nflip=first round avg msg length <=5; windows: pre r11-20, post r31-40")
