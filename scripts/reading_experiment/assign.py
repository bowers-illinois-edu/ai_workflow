#!/usr/bin/env python3
"""Decide by coin flip which proposed changes go into the copy Jake reads.

Several checks read one draft and each proposes changes. If someone chose
which to apply, the places he stops would tell us about that person's taste
rather than about the checks. A coin removes the choosing, and because the
coin's chance is known and reproducible from a seed, score.py can later ask
whether applying a change made any difference by flipping the same coins
again.

Two orderings matter and both are enforced here rather than left to whoever
runs this. The assignment is decided and written to disk before any text is
altered, so the session that applies the changes cannot pick them. And the
copy he reads carries no mark of which lines were altered, because a reader
who can see the treatment is no longer a reader.

Stdlib only, offline.
"""

import argparse
import hashlib
import json
import os
import random
import sys


def assign_findings(findings, seed):
    """One coin per finding. Returns the findings with an "arm" added.

    A separate Random seeded once, rather than the global one, so that
    anything else drawing random numbers in the same process cannot shift
    the assignment and break reproducibility from the recorded seed.
    """
    rng = random.Random(seed)
    out = []
    for f in sorted(findings, key=lambda x: str(x["id"])):
        row = dict(f)
        row["arm"] = "applied" if rng.random() < 0.5 else "held"
        out.append(row)
    return out


def apply_findings(text, rows):
    """Put the applied replacements into the text, one line at a time.

    Line-by-line rather than whole-document, because the join between his
    marked stops and the finding locations is by line number: a replacement
    that added or removed a line would silently move every finding below it.
    """
    lines = text.split("\n")
    for row in rows:
        if row["arm"] != "applied":
            continue
        i = row["line"] - 1
        if not (0 <= i < len(lines)) or row["quote"] not in lines[i]:
            raise ValueError(
                "finding %s: %r is not on line %d"
                % (row["id"], row["quote"], row["line"]))
        lines[i] = lines[i].replace(row["quote"], row["replacement"])
        if "\n" in row["replacement"]:
            raise ValueError("finding %s: replacement spans lines" % row["id"])
    return "\n".join(lines)


def sha256_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def run(draft_path, findings, seed, out_dir):
    """Assign, record, then apply. The order is the point of the function."""
    rows = assign_findings(findings, seed)

    os.makedirs(out_dir, exist_ok=True)
    assignment = os.path.join(out_dir, "assignment.json")
    with open(assignment, "w", encoding="ascii") as fh:
        json.dump({"seed": seed,
                   "draft": os.path.abspath(draft_path),
                   "draft_sha256": sha256_of(draft_path),
                   "rows": rows}, fh, indent=1)
        fh.flush()
        os.fsync(fh.fileno())

    with open(draft_path, encoding="utf-8") as fh:
        text = fh.read()
    reading_copy = os.path.join(out_dir, "reading_copy.tex")
    with open(reading_copy, "w", encoding="utf-8") as fh:
        fh.write(apply_findings(text, rows))

    return {"assignment": assignment, "reading_copy": reading_copy}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("draft")
    ap.add_argument("findings", help="JSON list of {id, line, quote, replacement, check}")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)

    with open(args.findings, encoding="utf-8") as fh:
        findings = json.load(fh)
    paths = run(args.draft, findings, args.seed, args.out_dir)
    applied = sum(1 for r in json.load(open(paths["assignment"]))["rows"]
                  if r["arm"] == "applied")
    print("findings: %d, applied: %d, held: %d"
          % (len(findings), applied, len(findings) - applied))
    print("assignment: %s" % paths["assignment"])
    print("reading copy: %s" % paths["reading_copy"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
