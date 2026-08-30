#!/usr/bin/env python3
"""Mechanical first pass for the style-audit skill.

Scans prose files for the named offenders in the global CLAUDE.md writing
rules, plus non-ASCII characters and dash-semicolon collisions. Every hit
is a CANDIDATE for the judgment pass, not a verdict: literal uses pass,
quotations pass, defined-and-glossed terms of art pass. The judgment pass
(SKILL.md section 1, pass 2) decides.

Skips fenced code blocks in .md/.qmd files and comment lines in .tex files;
--no-skip scans everything.

Usage:
  python3 style_scan.py FILE [FILE ...] [--no-skip] [--quiet]

Exit status: 0 no candidates, 2 candidates found, 1 usage error.
"""

import argparse
import re
import sys
import unicodedata

# (category, compiled pattern). Kept in one table so adding an offender is
# a one-line change. Patterns are deliberately eager: the cost of a false
# positive is one glance in the judgment pass; the cost of a false negative
# is a banned figure in print.
RAW_PATTERNS = [
    ("structural-metaphor", r"\bload-?bearing\b"),
    ("structural-metaphor", r"\bspine\b|\bbackbone\b|\bskeleton\b"),
    ("structural-metaphor", r"\bscaffold(?:ing|ed|s)?\b"),
    ("structural-metaphor", r"\bpillars?\b|\bcornerstones?\b|\bfoundational\b"),
    ("structural-metaphor", r"\bconnective tissue\b"),
    ("industrial-metaphor", r"\b(?:machinery|apparatus|engine|gears)\s+of\b"),
    ("infrastructure-metaphor", r"\bfirewalls?\b|\bguardrails?\b|\bsandbox(?:ed|ing|es)?\b"),
    ("infrastructure-metaphor", r"\bpipelines?\b|\bplumbing\b|\bthe stack\b"),
    # Commercial figures for intellectual gain and loss. "worth" is left to
    # the throat-clearing patterns, which already carry "it is worth noting";
    # a bare \bworth\b here would double-flag every one of those.
    ("commercial-metaphor", r"\bcosts?\b|\bcosting\b|\bcostly\b"),
    ("commercial-metaphor", r"\bbuys?\b|\bbought\b|\bbuying\b|\bpurchases?\b"),
    ("commercial-metaphor", r"\bpays?\s+(?:for|off|its\s+way|dividends)\b|\bpaid\s+for\b"),
    ("commercial-metaphor", r"\bafford(?:s|ed|ing)?\b"),
    ("commercial-metaphor", r"\bcheap(?:er|est|ly)?\b|\bexpensive\b|\bpric(?:e|ey|ing)\b"),
    ("commercial-metaphor", r"\binvest(?:s|ed|ing|ment)?\b|\bdividends?\b|\breturn\s+on\b"),
    ("commercial-metaphor", r"\bworth\s+(?:it|the|its|every)\b|\bnot\s+worth\b"),
    ("vague-evaluative", r"\b(?:is|are|was|were|seems?|looks?)\s+(?:appropriate|suitable|reasonable|warranted|justified|well-suited)\b"),
    ("vague-evaluative", r"\bmakes sense\b|\bthe right choice\b|\bcomfortabl[ye]\b|\bcomfortable margin\b"),
    ("vague-evaluative", r"\b(?:is|are|was|were)\s+(?:valid|robust|principled|natural)\b"),
    ("locative-figure", r"\breads?\s+onto\b|\bmaps?\s+onto\b|\breads?\s+(?:cleanly\s+)?off\b"),
    # "live" takes whatever preposition is handy, and the preposition is
    # incidental to the figure. Matching only "lives in" caught "the examples
    # live in regression" and slid past "some questions live at the edges"
    # three days later in the same document. "sit" is deliberately NOT
    # broadened here, but not for the reason this comment used to give. It
    # said a number really does sit at a distance from another number. On
    # 2026-08-30 Jake read a class note with 26 lines of it and wrote "in
    # general 'sit' and 'sat' are not useful words for the values that
    # summaries take," so that judgment was wrong. No pattern was added,
    # because a bare \bsits?\b would flag every literal use in a paper about
    # seating, and because the mechanism belongs to the judgment pass: the
    # plain verb is "is" or "are". The catalog and the first-reader persona
    # carry it as a worked example instead.
    ("locative-figure", r"\bliv(?:e|es|ed|ing)\s+(?:in|inside|within|at|on|among|amongst|between|beneath|underneath|under|above|over|across|through|beyond|near|alongside|behind)\b|\bsits?\s+across\b"),
    # The noun after the possessive is incidental: "earns its place" and
    # "earned its way" are the same figure as the catalogued "earn their
    # keep", and the narrow pattern let the first two through.
    ("idiom", r"\bearn(?:s|ed|ing)?\s+(?:its|their|his|her|your|our|my)\s+\w+\b|\bshor(?:e|ing)\s+up\b|\bhold\s+at\s+bay\b"),
    ("idiom", r"\bfold(?:s|ed|ing)?\s+in(?:to)?\b|\bwav(?:e|es|ed|ing)\s+away\b|\bkeep\s+faith\s+with\b"),
    ("idiom", r"\bwith\s+eyes\s+open\b|\bhand-?wav(?:e|ing|y)\b|\bwalk\s+the\s+list\b"),
    # An argument that "lands" --- named in SKILL.md section 6 as one of the
    # figures the catalog had missed, and matched by nothing until now. Bare
    # "land" is left out: as a noun and as a verb about ground it is almost
    # always literal.
    ("idiom", r"\b(?:lands|landed|landing)\b"),
    ("throat-clearing", r"\bit\s+is\s+(?:important|worth|interesting|crucial|essential|useful|instructive)\b"),
    # "worth" hung on a noun rather than on an expletive "it": a reason worth
    # stating, a point worth making, the failure mode worth naming. SKILL.md
    # names this family; only the "it is worth" form had a pattern.
    ("throat-clearing", r"\bworth\s+\w+ing\b"),
    ("throat-clearing", r"\bit\s+should\s+be\s+noted\b|\bnote\s+that\b|\bone\s+should\s+observe\b"),
    ("ornamental-transition", r"\b(?:moreover|furthermore)\b"),
    ("empty-hedge", r"\barguably\b|\bit\s+is\s+perhaps\b"),
    # Internal shorthand reporting a check the reader has never been shown.
    # "Guard passes", "scanner clean", "numbers match": each names a tool or a
    # comparison the writer knows and the reader has to be told. Say what was
    # checked and what the result means for the reader, or, when a check
    # passed and nothing follows from it, say nothing.
    ("internal-shorthand", r"\b(?:guard|scanner|linter|suite|build|freeze|pipeline|CI|render|check|checks|tests?)\s+(?:passes|passed|pass|is\s+green|are\s+green|green|clean|current)\b"),
    ("internal-shorthand", r"\b(?:numbers?|outputs?|figures?|results?)\s+match(?:es|ed)?\b"),
    ("internal-shorthand", r"\bascii\s+clean\b|\ball\s+green\b|\bstill\s+green\b|\bis\s+green\b"),
    # Bold run-in topic sentence opening a paragraph. scan_line works one
    # line at a time, so ^ anchors at line start without re.M; list bullets
    # ("- **...**") do not match, and they are house style in the
    # instruction files.
    ("bold-run-in-opener", r"^\*\*[^*]+[.?!]\*\*"),
]
PATTERNS = [(cat, re.compile(pat, re.I)) for cat, pat in RAW_PATTERNS]


def scan_line(path, lineno, line, findings):
    for cat, rx in PATTERNS:
        for m in rx.finditer(line):
            findings.append((path, lineno, cat, m.group(0)))
    for ch in line:
        if ord(ch) > 126:
            try:
                name = unicodedata.name(ch)
            except ValueError:
                name = "unnamed"
            findings.append((path, lineno, "unicode",
                             "U+%04X %s" % (ord(ch), name)))
    # An em-dash and a semicolon in one sentence is banned; one line is the
    # cheap approximation of one sentence.
    if "---" in line and ";" in line:
        findings.append((path, lineno, "dash-semicolon", line.strip()[:60]))


def scan_file(path, skip_regions):
    findings = []
    in_fence = False
    is_md = path.endswith((".md", ".qmd", ".Rmd", ".markdown"))
    is_tex = path.endswith((".tex", ".sty", ".cls"))
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, 1):
                if skip_regions and is_md:
                    if line.lstrip().startswith("```"):
                        in_fence = not in_fence
                        continue
                    if in_fence:
                        continue
                if skip_regions and is_tex and line.lstrip().startswith("%"):
                    continue
                scan_line(path, lineno, line, findings)
    except OSError as e:
        print("cannot read %s: %s" % (path, e), file=sys.stderr)
    return findings


def main():
    ap = argparse.ArgumentParser(description="Mechanical pass of the style-audit skill.")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--no-skip", action="store_true",
                    help="also scan code fences and TeX comments")
    ap.add_argument("--quiet", action="store_true",
                    help="summary only, no per-hit lines")
    args = ap.parse_args()

    all_findings = []
    for path in args.files:
        all_findings.extend(scan_file(path, not args.no_skip))

    counts = {}
    for path, lineno, cat, text in all_findings:
        counts[cat] = counts.get(cat, 0) + 1
        if not args.quiet:
            print("%s:%d: [%s] %s" % (path, lineno, cat, text))

    if all_findings:
        print("\n%d candidate(s): %s" % (
            len(all_findings),
            ", ".join("%s %d" % (c, counts[c]) for c in sorted(counts))))
        print("Candidates, not verdicts: run the judgment pass (SKILL.md section 1).")
        return 2
    print("no candidates found in %d file(s); the judgment pass still applies"
          % len(args.files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
