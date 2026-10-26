import re, json, glob, os, statistics as st
def load(p):
    out=[]
    for line in open(p, errors="ignore"):
        m=re.search(r'completed with result: (\{.*\})\s*$', line)
        if m:
            try: out.append(json.loads(m.group(1)))
            except: pass
    return out
def win(rs,a,b):
    w=[r for r in rs if a<=r["round_number"]<=b]
    msgs=[m for r in w for m in r["seller_messages"].values()]
    spr=[max(r["seller_asks"].values())-min(r["seller_asks"].values()) for r in w]
    tr=[t["price"] for r in w for t in r["trades"]]
    f=lambda x: round(st.mean(x),2) if x else None
    return dict(msg_len=f([len(m) for m in msgs]), short=f([len(m)<=3 for m in msgs]),
                spread=f(spr), price=f(tr), trades=len(tr))
for p in sorted(glob.glob("results/*/unified.log")):
    rs=load(p)
    if not rs: continue
    print(os.path.basename(os.path.dirname(p)))
    for a,b in [(11,20),(31,40)]: print(f"  r{a}-{b}", win(rs,a,b))
