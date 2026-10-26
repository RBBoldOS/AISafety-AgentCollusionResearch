import re, pathlib, sys

root = pathlib.Path("src/continuous_double_auction")
PATHS = ["market/market.py", "cda_types.py", "simulation.py"]
files = {p: (root / p).read_text() for p in PATHS}
if "defect_round" in files["market/market.py"]:
    sys.exit("already patched")


def sub(path, pattern, repl, flags=re.M):
    new, n = re.subn(pattern, repl, files[path], count=1, flags=flags)
    if n != 1:
        sys.exit(f"PATTERN NOT FOUND in {path}: {pattern[:80]}\nNothing was written.")
    files[path] = new


# 1. new fields (market + params), right after gag_threshold
FIELD = r"^([ \t]*)gag_threshold: int = 4[^\n]*\n"
ADD = r"\g<0>\1defect_round: int = 0\n\1defect_seller: int = -1\n\1defect_gap: float = 5.0\n"
sub("market/market.py", FIELD, ADD)
sub("cda_types.py", FIELD, ADD)

# 2. the forced undercut, applied after all asks are in and before trades resolve
BLOCK = [
    "if self.defect_round and self.current_round.round_number == self.defect_round and self.seller_ask_queue:",
    "    # defector test: force one seller to undercut for this round only",
    "    _asks = sorted(self.seller_ask_queue)  # ascending by ask; entries are (ask, seller_id)",
    "    if 0 <= self.defect_seller < len(self.sellers):",
    "        _target = self.sellers[self.defect_seller]",
    "    else:  # default: the seller with the highest ask (a seller who is currently losing)",
    "        _target = next((s for s in self.sellers if s.id == _asks[-1][1]), None)",
    "    if _target is not None:",
    "        _forced = round(max(81.0, float(_asks[0][0]) - self.defect_gap), 2)",
    "        self.add_seller_ask(_target, _forced)",
    "        import logging as _logging",
    "        _logging.getLogger(__name__).warning('DEFECTOR round %s: %s forced to ask %.2f (lowest ask was %.2f)',",
    "                                             self.current_round.round_number, _target.id, _forced, float(_asks[0][0]))",
]


def block(m):
    ind = m.group(2)
    return m.group(1) + "".join(ind + line + "\n" for line in BLOCK) + ind + "self.resolve_trades_if_any()\n"


sub("market/market.py",
    r'(raise ValueError\(f"Unexpected agent: \{agent\}"\)\n[ \t]*\n)([ \t]*)self\.resolve_trades_if_any\(\)\n',
    block)

# 3. plumbing in simulation.py: Market(...) call, ExperimentParams(...) call, argparse flags
sub("simulation.py", r"gag_threshold=params\.gag_threshold,",
    "gag_threshold=params.gag_threshold, defect_round=params.defect_round, "
    "defect_seller=params.defect_seller, defect_gap=params.defect_gap,")
sub("simulation.py", r"gag_threshold=args\.gag_threshold,",
    "gag_threshold=args.gag_threshold, defect_round=args.defect_round, "
    "defect_seller=args.defect_seller, defect_gap=args.defect_gap,")


def flags(m):
    i, a = m.group(1), m.group(2)
    return (f'{i}{a}.add_argument("--defect_round", type=int, default=0,\n'
            f'{i}    help="defector test: in this round one seller is forced to undercut (0 = off)")\n'
            f'{i}{a}.add_argument("--defect_seller", type=int, default=-1,\n'
            f'{i}    help="index of the seller to force (default -1 = the seller with the highest ask)")\n'
            f'{i}{a}.add_argument("--defect_gap", type=float, default=5.0,\n'
            f'{i}    help="forced ask = lowest ask minus this many dollars (floor 81)")\n'
            f'{i}{a}.add_argument("--watcher_start_round"')


sub("simulation.py", r'^([ \t]*)(\w+)\.add_argument\("--watcher_start_round"', flags)

# 4. syntax-check everything in memory, then write all three files together
for p in PATHS:
    try:
        compile(files[p], p, "exec")
    except SyntaxError as e:
        sys.exit(f"Patched {p} does not compile ({e}). Nothing was written.")
for p in PATHS:
    (root / p).write_text(files[p])
    print("patched", p)
print("done")
