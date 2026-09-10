#!/usr/bin/env python3
"""Reflow prose to one width so that line length says nothing about the text.

The replacements a check proposes are mostly longer than what they replace.
Applied to a hard-wrapped LaTeX file, that leaves the changed lines visibly
longer than the rest: in the first copy built for this experiment, the lines
carrying an applied change ran to a median of 81 characters against 72 for the
lines where a change was held back, and all six lines over 100 characters
carried an applied change. A reader who noticed would be reading a marked copy.

Reflowing every prose paragraph to one width removes that. It also moves the
line numbers, so this returns a map from each new line to the input lines its
words came from, and score.py uses that map to put a mark back on the right
finding.

What is left alone: comment lines, anything that begins a LaTeX command at the
start of a line, and everything inside a display or verbatim environment.
Reflowing those would change the document rather than its shape.

Stdlib only, offline.
"""

import argparse
import json
import re
import sys
import textwrap

# Environments whose contents are laid out by hand or by the compiler.
PROTECTED = {"equation", "equation*", "align", "align*", "gather", "gather*",
             "eqnarray", "eqnarray*", "verbatim", "lstlisting", "tabular",
             "tabular*", "tabularx", "array", "matrix", "bmatrix", "pmatrix",
             "figure", "table", "tikzpicture", "algorithmic", "algorithm",
             "minipage", "itemize", "enumerate", "description"}

BEGIN = re.compile(r"^\s*\\begin\{([^}]*)\}")
END = re.compile(r"^\s*\\end\{([^}]*)\}")


def _is_structural(line):
    """A line the wrapper must not fold into a paragraph."""
    s = line.strip()
    if not s or s.startswith("%"):
        return True
    return s.startswith("\\") or s.startswith("&") or s.startswith("$$")


def rewrap(text, width=72):
    """Return (wrapped_text, map from new line number to input line numbers)."""
    src = text.split("\n")
    out = []
    mapping = {}
    depth = 0
    i = 0

    def emit(line, sources):
        out.append(line)
        mapping[len(out)] = sorted(set(sources))

    while i < len(src):
        line = src[i]
        m = BEGIN.match(line)
        if m:
            depth += 1 if m.group(1) in PROTECTED else 0
            emit(line, [i + 1])
            i += 1
            continue
        m = END.match(line)
        if m:
            emit(line, [i + 1])
            if m.group(1) in PROTECTED:
                depth = max(0, depth - 1)
            i += 1
            continue
        if depth or _is_structural(line):
            emit(line, [i + 1])
            i += 1
            continue

        # A paragraph: consecutive plain-prose lines. Join, wrap, then walk
        # the character offsets to say which input lines each output line
        # drew from.
        start = i
        chunk = []
        while (i < len(src) and not _is_structural(src[i])
               and not BEGIN.match(src[i]) and not END.match(src[i])):
            chunk.append(src[i])
            i += 1

        joined = " ".join(part.strip() for part in chunk)
        spans, pos = [], 0
        for n, part in enumerate(chunk):
            piece = part.strip()
            spans.append((pos, pos + len(piece), start + n + 1))
            pos += len(piece) + 1

        wrapped = textwrap.wrap(joined, width=width,
                                break_long_words=False,
                                break_on_hyphens=False) or [""]
        cursor = 0
        for w in wrapped:
            begin = joined.find(w, cursor)
            if begin < 0:
                begin = cursor
            finish = begin + len(w)
            cursor = finish
            sources = [ln for (a, b, ln) in spans if a < finish and begin < b]
            emit(w, sources or [start + 1])

    return "\n".join(out), mapping


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("infile")
    ap.add_argument("--width", type=int, default=72)
    ap.add_argument("--out", required=True)
    ap.add_argument("--map-out", required=True)
    args = ap.parse_args(argv)

    text = open(args.infile, encoding="utf-8").read()
    wrapped, mapping = rewrap(text, args.width)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(wrapped)
    json.dump({str(k): v for k, v in mapping.items()},
              open(args.map_out, "w", encoding="ascii"), indent=1)

    lengths = [len(l) for l in wrapped.split("\n") if l.strip()]
    lengths.sort()
    print("wrote %s: %d lines, median length %d, longest %d"
          % (args.out, len(wrapped.split("\n")), lengths[len(lengths)//2],
             lengths[-1]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
