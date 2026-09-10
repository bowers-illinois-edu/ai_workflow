"""Tests for rewrap.py, written before it exists.

Jake asked whether he could reflow the file with gwap. He cannot, because the
comparison joins his marks to findings by line number. But the question
exposed the reason he wanted to: the replacements applied to the draft are
mostly longer than the text they replaced, so a changed line is a long line,
and six lines over 100 characters all carried an applied change while none of
the held ones did. Reading that copy, he would be reading a marked one.

So the file gets reflowed to one width by us, after the changes go in, and a
map records where each new line came from. What that has to guarantee:

1. No prose line is longer than the target width, so length says nothing.
2. Nothing inside verbatim, equation, align, or tabular is touched, and
   neither is a comment line, because reflowing those changes the document.
3. Blank lines survive, since they are what separate paragraphs in LaTeX.
4. No word is lost, added, or reordered.
5. Every output line maps to the input lines its text came from, so a mark on
   an output line can be traced back to the findings that sit on those input
   lines.

Stdlib only, offline.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rewrap  # noqa: E402


PROSE = """This is a first line of ordinary prose that runs on a while.
Here is a second line, and it is quite long as well, long enough to matter.
A third.

A new paragraph starts after the blank line above it.
"""

PROTECTED = """Some prose before the display.

\\begin{equation}
  a + b = c \\quad \\text{and this line is deliberately very long indeed yes}
\\end{equation}

% a comment line that is long enough that a wrapper would want to break it up
More prose after.
"""


class WidthTest(unittest.TestCase):
    def test_no_prose_line_exceeds_the_width(self):
        out, _m = rewrap.rewrap(PROSE, width=40)
        for line in out.split("\n"):
            if line.strip():
                self.assertLessEqual(len(line), 40, repr(line))

    def test_a_single_unbreakable_word_is_allowed_to_exceed(self):
        text = "short\n" + "x" * 80 + "\n"
        out, _m = rewrap.rewrap(text, width=40)
        self.assertIn("x" * 80, out)


class ProtectedTest(unittest.TestCase):
    def test_equation_bodies_are_untouched(self):
        out, _m = rewrap.rewrap(PROTECTED, width=40)
        self.assertIn("a + b = c \\quad \\text{and this line is deliberately very long indeed yes}", out)

    def test_comment_lines_are_untouched(self):
        out, _m = rewrap.rewrap(PROTECTED, width=40)
        self.assertIn("% a comment line that is long enough that a wrapper would want to break it up", out)

    def test_begin_and_end_lines_are_untouched(self):
        out, _m = rewrap.rewrap(PROTECTED, width=40)
        self.assertIn("\\begin{equation}", out)
        self.assertIn("\\end{equation}", out)


class ContentTest(unittest.TestCase):
    def test_no_word_is_lost_added_or_reordered(self):
        for text in (PROSE, PROTECTED):
            out, _m = rewrap.rewrap(text, width=40)
            self.assertEqual(out.split(), text.split())

    def test_blank_lines_survive(self):
        out, _m = rewrap.rewrap(PROSE, width=40)
        self.assertEqual(out.count("\n\n"), PROSE.count("\n\n"))


class MapTest(unittest.TestCase):
    def test_every_output_line_maps_to_at_least_one_input_line(self):
        out, m = rewrap.rewrap(PROSE, width=40)
        for n in range(1, len(out.split("\n")) + 1):
            if out.split("\n")[n - 1].strip():
                self.assertTrue(m.get(n), "output line %d maps to nothing" % n)

    def test_the_mapped_input_lines_contain_the_output_words(self):
        text = "alpha beta gamma delta\nepsilon zeta eta theta\n"
        out, m = rewrap.rewrap(text, width=14)
        src = text.split("\n")
        for n, line in enumerate(out.split("\n"), 1):
            if not line.strip():
                continue
            pool = " ".join(src[i - 1] for i in m[n]).split()
            for word in line.split():
                self.assertIn(word, pool)

    def test_an_untouched_line_maps_to_itself(self):
        out, m = rewrap.rewrap(PROTECTED, width=40)
        lines = out.split("\n")
        i = lines.index("\\begin{equation}") + 1
        self.assertEqual(m[i], [PROTECTED.split("\n").index("\\begin{equation}") + 1])


if __name__ == "__main__":
    unittest.main()
