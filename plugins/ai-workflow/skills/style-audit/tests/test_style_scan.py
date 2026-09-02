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


def strip_cats(line):
    """Categories the scanner assigns when inline code spans are stripped."""
    findings = []
    ss.scan_line("f", 1, line, findings, strip_inline_code=True)
    return {cat for (_p, _n, cat, _t) in findings}


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

    def test_structural_metaphor_catches_the_seam_family(self):
        # "seamless" says two parts join without saying what joined what or
        # what a reader would have noticed at the join. The noun and the
        # adverb are in the same pattern so a reworded sentence does not
        # escape. Pattern added 2026-09-02.
        self.assertIn("structural-metaphor", cats("a seamless transition"))
        self.assertIn("structural-metaphor",
                      cats("the seam between the two sections"))
        self.assertIn("structural-metaphor",
                      cats("the parts fit together seamlessly"))

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

    def test_locative_figure_catches_prepositions_other_than_in(self):
        """The figure is "an abstract noun dwelling somewhere", and the
        preposition it uses is incidental. An earlier pattern matched only
        "lives in", so it caught "the examples live in regression" and slid
        past "some questions live at the edges" written three days later in
        the same document. Both are the same offender: a question cannot
        dwell anywhere, and the plain verb ("some questions are about the
        largest values") is what the figure is standing in for."""
        for phrase in (
            "some questions live at the edges",
            "the interesting examples live inside regression",
            "the difficulty lives at the boundary",
            "the tension living within the model",
            "the hard cases lived among the outliers",
            "the assumption lives beneath the derivation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn("locative-figure", cats(phrase))

    def test_locative_figure_leaves_sits_plus_distance_alone(self):
        """Broadening "live" must not broaden "sit". A number really does sit
        at a distance from another number, and prose about where a summary
        sits relative to data is literal, not figurative. Only "sits across"
        is a named offender. Flagging every "sits close to" would bury the
        real hits in a document about summaries of one variable."""
        for phrase in (
            "the summary sits close to the data",
            "the mean now sits above nine of the ten values",
            "the fraction sits just above one half",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn("locative-figure", cats(phrase))
        self.assertIn("locative-figure", cats("the argument sits across both designs"))

    def test_throat_clearing_catches_worth_plus_gerund(self):
        """SKILL.md's throat-clearing entry already names "modifiers hung on a
        noun": a reason worth stating, a point worth making, a case worth
        noting. The scanner only had the expletive-"it" form, so "the failure
        mode worth naming" and "one thing worth having" went through. The
        deletion test is what condemns them: strike the modifier and the noun
        still stands, so the words were announcing that a claim matters
        instead of making it."""
        for phrase in (
            "the failure mode worth naming",
            "one thing worth having",
            "a reason worth stating",
            "a point worth making",
            "an observation worth flagging",
            "that is worth emphasizing",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn("throat-clearing", cats(phrase))

    def test_internal_shorthand_in_a_status_report(self):
        """A different offender from the rest of this catalog, and the one
        Jake named on 2026-08-29: not a figure of speech but a term that means
        something to the writer and nothing to the reader. "Guard passes",
        "scanner clean" and "numbers match" each name a check the reader has
        never been shown, so the status line needs a glossary to read. The fix
        is to say what was checked and what the result means for the reader,
        or to say nothing when the check passed."""
        for phrase in (
            "guard passes",
            "the guard passed",
            "scanner clean",
            "freeze current",
            "the test suite is green",
            "numbers match",
            "the output matches",
            "ASCII clean",
            "CI green",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn("internal-shorthand", cats(phrase))

    def test_internal_shorthand_leaves_explained_results_alone(self):
        """The offender is the unexplained shorthand, not the report. A
        sentence that says what was checked and what it means for the reader
        must survive, or the pattern would punish the fix."""
        for phrase in (
            "every number in the prose is the number R printed",
            "the note is still marked a draft, so nothing was published",
            "the script found none of the words on its list",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn("internal-shorthand", cats(phrase))

    def test_idiom_catches_the_whole_earn_its_x_family(self):
        """Third instance of one gap shape. The catalog names "earn their
        keep", so the pattern required the word "keep" and slid past "earns
        its place", "earned its way" and the rest. The figure is "X is
        justified" or "X is worth keeping", and the noun after the possessive
        is incidental to it, exactly as the preposition is incidental to
        "lives in"."""
        for phrase in (
            "these results earn their keep",
            "the pattern earns its place",
            "the longer derivation earned its way in",
            "that section is earning its keep",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn("idiom", cats(phrase))

    def test_idiom_catches_an_argument_that_lands(self):
        """SKILL.md section 6 names "an argument that lands" as one of the
        three figures whose absence from the catalog prompted moving the
        catalog out of the global CLAUDE.md, and yet no pattern matched it.
        The plain verbs it stands in for are "convinces", "works", or
        "succeeds". Literal landings are flagged and exonerated in pass 2,
        the same way "load-bearing wall" is."""
        for phrase in (
            "the argument lands",
            "that explanation landed with the reader",
            "only one of the analogies landed",
            "the landing of the point is what matters",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn("idiom", cats(phrase))

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


class TestInlineCodeSpans(unittest.TestCase):
    """Inline code is a skip region, like a fence and for the same reason: a
    word between code marks is being named, not used.

    This is not the scanner starting to judge. A literal "load-bearing wall"
    is still flagged, and so is an offender inside double quotes, because
    quoted prose is still prose. Only the code marks exempt, and only in
    markdown, since in LaTeX a backtick opens a quotation instead.

    The case that forced the change: on 2026-09-01 the gate caught an idiom
    in a reply, and the reply reporting which word it had caught quoted the
    word and was logged in turn. Without a way to name an offender, no
    report of one can be written.
    """

    def test_backticked_offender_is_skipped(self):
        self.assertIn("idiom", cats("the argument lands"))
        self.assertNotIn("idiom", strip_cats("the pattern for `lands` fired"))

    def test_quoted_offender_is_still_flagged(self):
        # Double quotes are prose. If this ever passes, someone has widened
        # the exemption from "code marks" to "any mention", and the scanner
        # has started deciding use against mention instead of skipping a
        # region --- which is pass 2's job, not the scanner's.
        self.assertIn("idiom", strip_cats('the pattern for "lands" fired'))

    def test_offender_outside_the_span_on_the_same_line_is_caught(self):
        self.assertIn("idiom",
                      strip_cats("`lands` fired because the argument lands"))

    def test_placeholder_does_not_join_the_words_around_it(self):
        # Contrived on purpose: "hold at bay" is an offender and "hold `y` at
        # bay" is not. Replacing the span with a space would close the gap and
        # invent a match the line never contained.
        self.assertNotIn("idiom", strip_cats("hold `y` at bay"))

    def test_placeholder_does_not_swallow_a_word_touching_the_span(self):
        # Also contrived. The placeholder is a non-word character so that
        # "costs" keeps the word boundary the backtick gave it. An underscore
        # would leave "costs~" as one word and hide a true positive.
        self.assertIn("commercial-metaphor", strip_cats("it costs`*` nothing"))

    def test_unicode_inside_a_span_is_exempt_like_a_fence(self):
        # A fence already exempts unicode, and inline code does the same, so
        # the rule stays "code is exempt" rather than splitting by category.
        # What that gives up is a stray em dash between code marks, which now
        # goes unrecorded.
        line = "an em dash `\u2014` between code marks"
        self.assertIn("unicode", cats(line))
        self.assertNotIn("unicode", strip_cats(line))

    def test_markdown_file_strips_inline_code_only_when_skipping(self):
        path = write_temp("The regression `lands` in section 3.\n", ".md")
        try:
            skipped = ss.scan_file(path, skip_regions=True)
            scanned_all = ss.scan_file(path, skip_regions=False)
        finally:
            os.remove(path)
        self.assertEqual(skipped, [])
        self.assertTrue(any(c == "idiom" for (_p, _n, c, _t) in scanned_all))

    def test_tex_file_keeps_its_backticks(self):
        # In LaTeX a backtick opens a quotation, so deleting the text between
        # two of them would delete real prose. Only markdown gets the
        # exemption.
        path = write_temp("The argument `lands` in section 3.\n", ".tex")
        try:
            findings = ss.scan_file(path, skip_regions=True)
        finally:
            os.remove(path)
        self.assertTrue(any(c == "idiom" for (_p, _n, c, _t) in findings))


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
