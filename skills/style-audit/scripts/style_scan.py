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
    ("vague-evaluative", r"\b(?:is|are|was|were|seems?|looks?)\s+(?:appropriate|suitable|reasonable|warranted|justified|well-suited)\b"),
    ("vague-evaluative", r"\bmakes sense\b|\bthe right choice\b|\bcomfortabl[ye]\b|\bcomfortable margin\b"),
    ("vague-evaluative", r"\b(?:is|are|was|were)\s+(?:valid|robust|principled|natural)\b"),
    ("locative-figure", r"\breads?\s+onto\b|\bmaps?\s+onto\b|\breads?\s+(?:cleanly\s+)?off\b"),
    ("locative-figure", r"\blives?\s+in\b|\bsits?\s+across\b"),
    ("idiom", r"\bearns?\s+(?:its|their)\s+keep\b|\bshor(?:e|ing)\s+up\b|\bhold\s+at\s+bay\b"),
    ("idiom", r"\bfold(?:s|ed|ing)?\s+in(?:to)?\b|\bwav(?:e|es|ed|ing)\s+away\b|\bkeep\s+faith\s+with\b"),
    ("idiom", r"\bwith\s+eyes\s+open\b|\bhand-?wav(?:e|ing|y)\b|\bwalk\s+the\s+list\b"),
    ("throat-clearing", r"\bit\s+is\s+(?:important|worth|interesting|crucial|essential|useful|instructive)\b"),
    ("throat-clearing", r"\bit\s+should\s+be\s+noted\b|\bnote\s+that\b|\bone\s+should\s+observe\b"),
    ("ornamental-transition", r"\b(?:moreover|furthermore)\b"),
    ("empty-hedge", r"\barguably\b|\bit\s+is\s+perhaps\b"),
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
