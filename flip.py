import re, json, glob
for p in sorted(glob.glob("results/*S3_silent_watched*/unified.log")+glob.glob("results/*S2_late21*/unified.log")):
    rs=[]
    for line in open(p, errors="ignore"):
        m=re.search(r'completed with result: (\{.*\})\s*$', line)
        if m: rs.append(json.loads(m.group(1)))
    print(p.split("/")[1], [(r["round_number"], round(sum(len(x) for x in r["seller_messages"].values())/max(1,len(r["seller_messages"])))) for r in rs if 18<=r["round_number"]<=28])
