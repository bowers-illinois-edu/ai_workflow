#!/usr/bin/env python3
"""Pool the checks' findings and settle the ones that land on the same words.

Three checks read one draft, so two of them sometimes flag the same phrase and
propose different replacements. Both cannot be applied: the first replacement
destroys the text the second quotes.

Whoever chooses between them decides part of what Jake reads, so the choice is
made by a coin from the recorded seed rather than by the session running the
experiment. Otherwise the places he stops would report this session's taste in
sentences, which is not what anyone wants to measure.

Stdlib only, offline.
"""

import argparse
import json
import random
import sys


def _span(finding, lines):
    """Where the quoted text sits on its line, as (start, end)."""
    i = finding["line"] - 1
    line = lines[i] if 0 <= i < len(lines) else ""
    start = line.find(finding["quote"])
    if start < 0:
        raise ValueError("finding %s: %r is not on line %d"
                         % (finding["id"], finding["quote"], finding["line"]))
    return start, start + len(finding["quote"])


def resolve(findings, lines, seed):
    """Return (kept, dropped). Overlapping findings are settled by a coin.

    Findings are sorted by id first so that the order they arrive in cannot
    change the result, and the coin is drawn from a Random seeded here rather
    than the global one, so nothing else in the process can shift it.
    """
    rng = random.Random(seed)
    ordered = sorted(findings, key=lambda f: str(f["id"]))

    kept, dropped = [], []
    for f in ordered:
        start, end = _span(f, lines)
        clash = None
        for g in kept:
            if g["line"] != f["line"]:
                continue
            gs, ge = _span(g, lines)
            if start < ge and gs < end:
                clash = g
                break
        if clash is None:
            kept.append(f)
            continue
        # A coin decides which of the two stays, so neither check is favored.
        if rng.random() < 0.5:
            kept[kept.index(clash)] = f
            loser = dict(clash)
            loser["dropped_for"] = f["id"]
        else:
            loser = dict(f)
            loser["dropped_for"] = clash["id"]
        dropped.append(loser)
    return kept, dropped


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("draft")
    ap.add_argument("findings", nargs="+", help="one or more JSON finding files")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dropped-out", required=True)
    args = ap.parse_args(argv)

    lines = open(args.draft, encoding="utf-8").read().split("\n")
    findings = []
    for path in args.findings:
        findings.extend(json.load(open(path, encoding="utf-8")))

    kept, dropped = resolve(findings, lines, args.seed)
    json.dump(kept, open(args.out, "w", encoding="ascii"), indent=1)
    json.dump(dropped, open(args.dropped_out, "w", encoding="ascii"), indent=1)

    by_check = {}
    for r in kept:
        by_check[r["check"]] = by_check.get(r["check"], 0) + 1
    print("pooled %d findings, kept %d, dropped %d to overlap"
          % (len(findings), len(kept), len(dropped)))
    for check in sorted(by_check):
        print("   %-16s %d" % (check, by_check[check]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
