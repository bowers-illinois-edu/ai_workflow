#!/usr/bin/env python3
"""Unit tests for style_scan.py, the style-audit mechanical first pass.

The substantive point of this scanner (SKILL.md section 1) is NOT to decide
whether a word is a style violation --- that is the judgment pass, pass 2.
The scanner's job is to make the first pass cheap and complete: flag every
CANDIDATE, over-including on purpose, so pass 2 has a short list to triage.
Two design facts the tests must protect:

  * Every named-offender category from the global CLAUDE.md is matched
    (structural / industrial / infrastructure metaphors, vague evaluatives,
    locative figures, idioms, throat-clearing, ornamental transitions, empty
    hedges), plus non-ASCII characters and em-dash + semicolon collisions.
  * A LITERAL use is still flagged. "load-bearing wall" is a real wall, and
    pass 2 will exonerate it --- but the scanner must surface it, because the
    scanner does not judge. A test that expected the scanner to skip literal
    uses would encode the opposite of the design.

The exit-status contract (0 = no candidates, 2 = candidates found) is what a
Makefile gates on, so it is tested through main().

Run: python3 test_style_scan.py     (or via the repo-root Makefile: make test)
"""

import contextlib
import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
import style_scan as ss  # noqa: E402


def cats(line):
    """Categories the scanner assigns to a single line."""
    findings = []
    ss.scan_line("f", 1, line, findings)
    return {cat for (_p, _n, cat, _t) in findings}


def texts(line):
    """Matched text fragments the scanner reports for a single line."""
    findings = []
    ss.scan_line("f", 1, line, findings)
    return [t for (_p, _n, _c, t) in findings]


def write_temp(text, suffix):
    """Write text to a temp file and return its path (caller removes it)."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


class TestNamedOffenders(unittest.TestCase):
    """One true positive per category from the global CLAUDE.md lists. Each
    asserts the category is present, not that it is the only one."""

    def test_structural_metaphor(self):
        self.assertIn("structural-metaphor", cats("This assumption is load-bearing."))
        self.assertIn("structural-metaphor", cats("the spine of the argument"))

    def test_industrial_metaphor(self):
        self.assertIn("industrial-metaphor", cats("the machinery of inference"))

    def test_infrastructure_metaphor(self):
        self.assertIn("infrastructure-metaphor",
                      cats("a firewall between the model and the data"))
        self.assertIn("infrastructure-metaphor", cats("the pipeline cleans the data"))

    def test_vague_evaluative(self):
        self.assertIn("vague-evaluative", cats("this choice is appropriate here"))
        self.assertIn("vague-evaluative", cats("the estimator is robust"))

    def test_locative_figure(self):
        self.assertIn("locative-figure", cats("the framework maps onto the design"))
        self.assertIn("locative-figure", cats("the theory lives in the data"))

    def test_idiom(self):
        self.assertIn("idiom", cats("these results shore up the claim"))

    def test_throat_clearing(self):
        self.assertIn("throat-clearing", cats("it is important to control the error"))
        self.assertIn("throat-clearing", cats("Note that the estimator is unbiased."))

    def test_ornamental_transition(self):
        self.assertIn("ornamental-transition", cats("Moreover, the result holds."))

    def test_empty_hedge(self):
        self.assertIn("empty-hedge", cats("this is arguably the best approach"))

    def test_commercial_metaphor(self):
        # The sentences that prompted this category, caught by Jake 2026-08-26
        # in a teaching document: an intellectual gain and an intellectual loss
        # both described as money changing hands.
        self.assertIn("commercial-metaphor",
                      cats("Two warnings, because both of them cost me an hour."))
        self.assertIn("commercial-metaphor",
                      cats("the comparison tells you what the line bought you"))
        # The rest of the family named in the same catalog entry.
        self.assertIn("commercial-metaphor",
                      cats("how many people did na.omit() cost us"))
        self.assertIn("commercial-metaphor",
                      cats("we cannot afford the extra assumption"))
        self.assertIn("commercial-metaphor",
                      cats("the second pass is cheap and the third is expensive"))
        self.assertIn("commercial-metaphor",
                      cats("the longer derivation pays for itself"))
        self.assertIn("commercial-metaphor",
                      cats("this investment in notation pays dividends later"))

    def test_commercial_metaphor_flags_literal_money_too(self):
        # Same contract as the load-bearing wall below: a paper genuinely about
        # program costs is flagged and then exonerated in pass 2. The scanner
        # must not try to tell the two apart.
        self.assertIn("commercial-metaphor",
                      cats("The program cost 4.2 million dollars per district."))


class TestScannerDoesNotJudge(unittest.TestCase):
    """SKILL.md 1: the scanner flags candidates, not verdicts. A literal use
    must STILL be flagged; pass 2, not the scanner, exonerates it."""

    def test_literal_use_is_still_flagged(self):
        # A real wall is a literal, legitimate use. The scanner flags it anyway;
        # if this ever passed silently the scanner would be judging.
        self.assertIn("structural-metaphor",
                      cats("We repaired the load-bearing wall in the lab."))


class TestUnicodeAndPunctuation(unittest.TestCase):

    def test_non_ascii_flagged_with_codepoint(self):
        # The \u2014 escape below is a unicode em dash --- exactly what the
        # ASCII rule forbids. Writing it as an escape keeps THIS file ASCII.
        line = "an em dash \u2014 in the text"
        self.assertIn("unicode", cats(line))
        self.assertTrue(any("U+2014" in t for t in texts(line)))

    def test_dash_semicolon_collision_flagged(self):
        # Global CLAUDE.md: never an em-dash and a semicolon in one sentence.
        self.assertIn("dash-semicolon", cats("one clause --- and a second; a third"))


class TestSkipRegions(unittest.TestCase):
    """SKILL.md 1: skip fenced code in markdown and comment lines in LaTeX by
    default; --no-skip (skip_regions=False) scans everything."""

    def test_markdown_fence_skipped_by_default(self):
        md = "\n".join([
            "This is load-bearing text.",   # body: flagged
            "```",
            "code with a spine inside the fence",   # fenced: skipped by default
            "```",
            "Outside the machinery of things.",     # body: flagged
        ])
        path = write_temp(md, ".md")
        try:
            skipped = ss.scan_file(path, skip_regions=True)
            scanned_all = ss.scan_file(path, skip_regions=False)
        finally:
            os.remove(path)
        # Default: the fenced "spine" is not among the findings.
        self.assertFalse(any("spine" in t for (_p, _n, _c, t) in skipped))
        # --no-skip: it is.
        self.assertTrue(any("spine" in t for (_p, _n, _c, t) in scanned_all))
        self.assertGreater(len(scanned_all), len(skipped))

    def test_tex_comment_skipped_by_default(self):
        tex = "\n".join([
            "% this comment is load-bearing and should be skipped",
            "The real spine of the paper is section 3.",
        ])
        path = write_temp(tex, ".tex")
        try:
            skipped = ss.scan_file(path, skip_regions=True)
            scanned_all = ss.scan_file(path, skip_regions=False)
        finally:
            os.remove(path)
        self.assertFalse(any("load" in t.lower() for (_p, _n, _c, t) in skipped))
        self.assertTrue(any("load" in t.lower() for (_p, _n, _c, t) in scanned_all))


class TestExitStatus(unittest.TestCase):
    """The Makefile gate: main() returns 2 when candidates exist, 0 when the
    scan is clean (docstring of style_scan.py; SKILL.md 1)."""

    def _run_main(self, path):
        argv = sys.argv
        sys.argv = ["style_scan.py", path]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                return ss.main()
        finally:
            sys.argv = argv

    def test_candidates_return_2(self):
        path = write_temp("This assumption is load-bearing.\n", ".md")
        try:
            self.assertEqual(self._run_main(path), 2)
        finally:
            os.remove(path)

    def test_clean_text_returns_0(self):
        # Plain, ASCII, no listed offender, no dash-semicolon: nothing to flag.
        path = write_temp("The estimator has low variance in simulations.\n", ".md")
        try:
            self.assertEqual(self._run_main(path), 0)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
