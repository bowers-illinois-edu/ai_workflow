"""Tests for pool.py, written before it exists.

Three checks read the same draft, so two of them sometimes flag the same words
and propose different fixes. Applying both is impossible: the first
replacement destroys the text the second quotes. Someone has to choose, and
if that someone is the session running the experiment then the places Jake
stops report that session's taste.

So the choice is made by a coin from the recorded seed, and this file pins
down what that has to guarantee:

1. Findings that do not overlap all survive, whatever check they came from.
2. When two overlap, exactly one survives.
3. The same seed keeps the same one, so the run can be rebuilt from the record.
4. Over many seeds each of the two does survive sometimes, which is what
   makes it a coin rather than a preference for one check.
5. The dropped findings are returned rather than discarded, so the record
   shows what was set aside and why.

Stdlib only, offline.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pool  # noqa: E402


LINES = ["untouched line zero",
         "the cost of hedging is small and the signal sits here",
         "a second line with one fault in it"]

A = {"id": "a1", "line": 2, "quote": "the cost of hedging",
     "replacement": "the power given up", "check": "scanner"}
B = {"id": "b1", "line": 2, "quote": "cost of hedging is small",
     "replacement": "loss from using both is small", "check": "questions"}
C = {"id": "c1", "line": 2, "quote": "the signal sits",
     "replacement": "the signal is", "check": "first-reader"}
D = {"id": "d1", "line": 3, "quote": "one fault",
     "replacement": "a single fault", "check": "questions"}


class NoOverlapTest(unittest.TestCase):
    def test_findings_on_different_lines_all_survive(self):
        kept, dropped = pool.resolve([A, D], LINES, seed=1)
        self.assertEqual(sorted(r["id"] for r in kept), ["a1", "d1"])
        self.assertEqual(dropped, [])

    def test_two_findings_on_one_line_that_do_not_overlap_both_survive(self):
        kept, dropped = pool.resolve([A, C], LINES, seed=1)
        self.assertEqual(sorted(r["id"] for r in kept), ["a1", "c1"])
        self.assertEqual(dropped, [])


class OverlapTest(unittest.TestCase):
    def test_exactly_one_of_an_overlapping_pair_survives(self):
        kept, dropped = pool.resolve([A, B], LINES, seed=1)
        self.assertEqual(len(kept), 1)
        self.assertEqual(len(dropped), 1)
        self.assertNotEqual(kept[0]["id"], dropped[0]["id"])

    def test_the_same_seed_keeps_the_same_one(self):
        first = pool.resolve([A, B], LINES, seed=4)[0][0]["id"]
        again = pool.resolve([A, B], LINES, seed=4)[0][0]["id"]
        self.assertEqual(first, again)

    def test_both_survive_under_some_seed(self):
        """A rule that always keeps the scanner is a preference, not a coin."""
        survivors = {pool.resolve([A, B], LINES, seed=s)[0][0]["id"]
                     for s in range(60)}
        self.assertEqual(survivors, {"a1", "b1"})

    def test_a_dropped_finding_says_what_it_lost_to(self):
        _kept, dropped = pool.resolve([A, B], LINES, seed=1)
        self.assertIn("dropped_for", dropped[0])

    def test_survivors_can_all_be_applied_together(self):
        """The point of the whole file: no collision survives resolution."""
        kept, _dropped = pool.resolve([A, B, C, D], LINES, seed=3)
        text = "\n".join(LINES)
        import assign
        rows = [dict(r, arm="applied") for r in kept]
        assign.apply_findings(text, rows)  # raises if a quote has gone


class OrderTest(unittest.TestCase):
    def test_input_order_does_not_change_the_result(self):
        a = pool.resolve([A, B, C, D], LINES, seed=8)[0]
        b = pool.resolve([D, C, B, A], LINES, seed=8)[0]
        self.assertEqual(sorted(r["id"] for r in a),
                         sorted(r["id"] for r in b))


if __name__ == "__main__":
    unittest.main()
