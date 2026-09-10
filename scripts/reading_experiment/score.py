#!/usr/bin/env python3
"""Compare where Jake stopped against which changes the coin applied.

Jake objected, correctly, to a confidence interval printed beside a count of
phrases he happened to quote back: nothing there was drawn by a process
anyone could repeat, so there was nothing for an interval to describe.

Here the objection does not apply. assign.py flipped a coin for each proposed
change and we know its chance, because we set it. Under the hypothesis that
applying a change made no difference to whether he stopped there, his stops
would have fallen where they fell whichever way the coins had landed. So we
flip the same coins again, thousands of times, and count how often a re-flip
separates the two groups as far as the real assignment did. Nothing is
assumed about how his stops are distributed.

Two things are dropped before the comparison, and both are about what he
actually read. A stop he marked past the line where he quit is dropped,
because he never read it. And a location past that line leaves the comparison
too: he cannot stop where he did not read, so counting it as a place he did
not stop would credit the arm it happens to sit in.

Stdlib only, offline.
"""

import argparse
import json
import random
import sys


def read_stops(path):
    """Read the file the neovim mapping writes: line numbers and a quit marker.

    A line that is neither a comment nor a number raises rather than being
    skipped, because a silently dropped line number is indistinguishable from
    a place Jake did not stop, and that is the one error this comparison
    cannot survive.
    """
    stops = set()
    quit_line = None
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            marker = line[1:].strip()
            if marker.startswith("quit:"):
                value = marker[len("quit:"):].strip()
                if value.isdigit():
                    quit_line = int(value)
            continue
        first = line.split()[0]
        if not first.isdigit():
            raise ValueError("not a line number in %s: %r" % (path, line))
        stops.add(int(first))
    return stops, quit_line


def translate(stops, line_map):
    """Carry marks made on the reflowed copy back to the draft's line numbers.

    A reflowed line can draw its words from more than one draft line, so one
    mark can land on more than one. A mark the map does not know is kept as
    itself rather than dropped: it then shows up in the summary as a stop at
    no location, which is visible, whereas a dropped mark is not.
    """
    if not line_map:
        return set(stops)
    out = set()
    for s in stops:
        out |= set(line_map.get(s, [s]))
    return out


def usable_stops(stops, quit_line):
    """Split his marked stops into the ones he read and the ones he did not."""
    if quit_line is None:
        return set(stops), set()
    kept = {s for s in stops if s <= quit_line}
    return kept, set(stops) - kept


def usable_rows(rows, quit_line):
    if quit_line is None:
        return list(rows)
    return [r for r in rows if r["line"] <= quit_line]


def difference(rows, stops):
    """Stop rate where changes were applied, minus the rate where they were not."""
    applied = [r for r in rows if r["arm"] == "applied"]
    held = [r for r in rows if r["arm"] == "held"]
    if not applied or not held:
        return 0.0
    a = sum(1 for r in applied if r["line"] in stops) / len(applied)
    h = sum(1 for r in held if r["line"] in stops) / len(held)
    return a - h


def shuffled_arms(rows, reps, seed):
    """Re-flip the coins, keeping the number applied at what really happened.

    Holding that number fixed is what makes each shuffle a world that could
    have occurred under the same procedure.
    """
    rng = random.Random(seed)
    arms = [r["arm"] for r in rows]
    for _ in range(reps):
        shuffled = list(arms)
        rng.shuffle(shuffled)
        yield shuffled


def permutation_p(rows, stops, reps, seed):
    observed = difference(rows, stops)
    count = 0
    for arms in shuffled_arms(rows, reps, seed):
        perm = [dict(r, arm=arms[i]) for i, r in enumerate(rows)]
        if abs(difference(perm, stops)) >= abs(observed):
            count += 1
    return count / reps


def summarize(rows, stops, quit_line, reps, seed):
    kept_stops, unread_stops = usable_stops(stops, quit_line)
    kept_rows = usable_rows(rows, quit_line)
    at_location = {s for s in kept_stops if any(r["line"] == s for r in kept_rows)}

    applied = [r for r in kept_rows if r["arm"] == "applied"]
    held = [r for r in kept_rows if r["arm"] == "held"]
    return {
        "locations_read": len(kept_rows),
        "applied": len(applied),
        "held": len(held),
        "stops_read": len(kept_stops),
        "stops_after_quit_line": len(unread_stops),
        "stops_at_no_location": len(kept_stops) - len(at_location),
        "stop_rate_applied": (sum(1 for r in applied if r["line"] in kept_stops)
                              / len(applied)) if applied else None,
        "stop_rate_held": (sum(1 for r in held if r["line"] in kept_stops)
                           / len(held)) if held else None,
        "difference": difference(kept_rows, kept_stops),
        "p_value": permutation_p(kept_rows, kept_stops, reps, seed),
        "reps": reps,
    }


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("assignment", help="assignment.json from assign.py")
    ap.add_argument("stops", help="file of line numbers Jake stopped at, one per line")
    ap.add_argument("--quit-line", type=int, default=None)
    ap.add_argument("--line-map", default=None,
                    help="line_map.json from rewrap.py, when he read a reflowed copy")
    ap.add_argument("--reps", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args(argv)

    rows = json.load(open(args.assignment))["rows"]
    stops, quit_from_file = read_stops(args.stops)
    quit_line = args.quit_line if args.quit_line is not None else quit_from_file

    line_map = None
    if args.line_map:
        line_map = {int(k): v for k, v in json.load(open(args.line_map)).items()}
        stops = translate(stops, line_map)
        if quit_line is not None:
            quit_line = max(translate({quit_line}, line_map))

    out = summarize(rows, stops, quit_line, args.reps, args.seed)
    for k in ("locations_read", "applied", "held", "stops_read",
              "stops_after_quit_line", "stops_at_no_location",
              "stop_rate_applied", "stop_rate_held", "difference", "p_value"):
        print("%-24s %s" % (k, out[k]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
