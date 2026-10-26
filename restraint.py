import json, re, sys, glob, os, statistics as st


def find_runs(pattern):
    found = {}
    for d in sorted(glob.glob("results/*")):
        m = re.search(rf"_(?:{pattern})-seed(\d+)$", d)
        if m and os.path.isfile(os.path.join(d, "collusion_metrics.json")) \
                and os.path.isfile(os.path.join(d, "unified.log")):
            found[int(m.group(1))] = d
    return dict(sorted(found.items()))


def rounds(d):
    for line in open(os.path.join(d, "unified.log"), errors="ignore"):
        m = re.search(r"Auction round (\d+) completed with result: (\{.*\})", line)
        if m:
            yield json.loads(m.group(2))


for pat in sys.argv[1:] or ["S2_late16"]:
    print(f"\n=== {pat}: how cheaply could a losing seller have won a sale? (rounds 11-30)")
    print(f"{'seed':>4} {'loser-rounds':>12} {'median cut (cents)':>19} {'median $ at stake':>18}")
    for s, d in find_runs(pat).items():
        cuts, stakes = [], []
        for r in rounds(d):
            if not (11 <= r["round_number"] <= 30) or not r["trades"]:
                continue
            winners = {t["seller_id"] for t in r["trades"]}
            m = max(r["seller_asks"][w] for w in winners)       # highest winning ask
            for seller, ask in r["seller_asks"].items():
                if seller not in winners and ask >= m:
                    cuts.append(round((ask - m + 0.01) * 100))   # cents needed to undercut the marginal winner
                    stakes.append(m - 0.01 - 80.0)               # approx profit on that sale (cost 80)
        if cuts:
            print(f"{s:>4} {len(cuts):>12} {st.median(cuts):>19.0f} {st.median(stakes):>18.2f}")
        else:
            print(f"{s:>4} {'no trades in window':>12}")
