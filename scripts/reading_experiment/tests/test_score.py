"""Tests for score.py, written before it exists.

Jake objected, correctly, to a confidence interval printed beside a count of
phrases he happened to quote: nothing there was drawn by a process anyone
could repeat, so there was nothing for an interval to describe.

Here the objection does not apply, and the reason is the point of this file.
The coin flips in assign.py ARE the repeatable process. We know the chance
each proposal had of being applied, because we set it. So the null hypothesis
"applying a change made no difference to whether Jake stopped there" can be
tested by re-flipping the same coins many times and asking how often the
re-flip separates the two groups as far as the real assignment did. Nothing is
assumed about how stops are distributed.

What each test pins down:

1. The test statistic is the difference in stop rate between the locations
   that were changed and the locations that were left alone.
2. Re-randomization uses the same number of applied locations as really
   occurred, so the shuffled worlds are worlds that could have happened.
3. A p-value of 1 comes back when the stops are spread evenly, and a small one
   when every stop sits in one arm.
4. A stop Jake marked past his quit line is dropped, because he never read it.
5. A stop that matches no location is counted for the record and excluded from
   the comparison, since it belongs to neither arm.

Stdlib only, offline.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import score  # noqa: E402


def rows(applied_lines, held_lines):
    out = [{"id": "a%d" % n, "line": n, "arm": "applied"} for n in applied_lines]
    out += [{"id": "h%d" % n, "line": n, "arm": "held"} for n in held_lines]
    return out


class StatisticTest(unittest.TestCase):
    def test_difference_is_applied_rate_minus_held_rate(self):
        r = rows([1, 2], [3, 4])
        # He stopped at both held locations and neither applied one.
        d = score.difference(r, stops={3, 4})
        self.assertAlmostEqual(d, 0.0 - 1.0)

    def test_no_stops_gives_a_difference_of_zero(self):
        self.assertAlmostEqual(score.difference(rows([1], [2]), stops=set()), 0.0)


class PermutationTest(unittest.TestCase):
    def test_even_spread_gives_a_large_p_value(self):
        r = rows([1, 2, 3, 4], [5, 6, 7, 8])
        p = score.permutation_p(r, stops={1, 2, 5, 6}, reps=2000, seed=1)
        self.assertGreater(p, 0.5)

    def test_all_stops_in_one_arm_gives_a_small_p_value(self):
        r = rows(list(range(1, 11)), list(range(11, 21)))
        p = score.permutation_p(r, stops=set(range(11, 21)), reps=2000, seed=1)
        self.assertLess(p, 0.01)

    def test_shuffles_keep_the_number_of_applied_locations_fixed(self):
        r = rows([1, 2, 3], [4, 5])
        for arms in score.shuffled_arms(r, reps=200, seed=2):
            self.assertEqual(sum(1 for a in arms if a == "applied"), 3)

    def test_the_same_seed_reproduces_the_p_value(self):
        r = rows([1, 2, 3], [4, 5, 6])
        a = score.permutation_p(r, stops={1, 4}, reps=500, seed=9)
        b = score.permutation_p(r, stops={1, 4}, reps=500, seed=9)
        self.assertEqual(a, b)


class ReadingTest(unittest.TestCase):
    def test_stops_after_the_quit_line_are_dropped(self):
        r = rows([1, 2], [3, 4])
        kept, dropped = score.usable_stops({1, 4}, quit_line=2)
        self.assertEqual(kept, {1})
        self.assertEqual(dropped, {4})

    def test_no_quit_line_keeps_everything(self):
        kept, dropped = score.usable_stops({1, 9}, quit_line=None)
        self.assertEqual(kept, {1, 9})
        self.assertEqual(dropped, set())

    def test_locations_past_the_quit_line_leave_the_comparison(self):
        """He cannot stop where he never read, so those rows carry no
        information and must not count as places he did not stop."""
        r = rows([1, 50], [2, 60])
        kept = score.usable_rows(r, quit_line=10)
        self.assertEqual(sorted(x["line"] for x in kept), [1, 2])

    def test_a_stop_matching_no_location_is_reported_not_silently_dropped(self):
        r = rows([1], [2])
        summary = score.summarize(r, stops={1, 99}, quit_line=None,
                                  reps=200, seed=1)
        self.assertEqual(summary["stops_at_no_location"], 1)


class StopsFileTest(unittest.TestCase):
    """The neovim mapping writes stops.md. Reading it back is where a silent
    mistake would do the most damage, because a dropped line number would
    look exactly like a place he did not stop."""

    def parse(self, text):
        import tempfile, os
        d = tempfile.mkdtemp()
        p = os.path.join(d, "stops.md")
        with open(p, "w") as fh:
            fh.write(text)
        return score.read_stops(p)

    def test_line_numbers_and_quit_line_are_both_read(self):
        stops, quit_line = self.parse(
            "# line  note\n42  undefined term\n900  \n# quit: 1200\n")
        self.assertEqual(stops, {42, 900})
        self.assertEqual(quit_line, 1200)

    def test_a_file_with_no_quit_marker_gives_none(self):
        stops, quit_line = self.parse("# line  note\n7  x\n")
        self.assertEqual(stops, {7})
        self.assertIsNone(quit_line)

    def test_the_placeholder_quit_line_is_not_read_as_a_number(self):
        """The header the mapping writes contains "# quit: <line>"."""
        stops, quit_line = self.parse("# line  note\n# quit: <line>\n5  x\n")
        self.assertEqual(stops, {5})
        self.assertIsNone(quit_line)

    def test_a_line_that_is_not_a_number_is_an_error_not_a_skip(self):
        with self.assertRaises(ValueError):
            self.parse("# line  note\nsomewhere near the top  x\n")


class LineMapTest(unittest.TestCase):
    """The copy Jake reads is reflowed, so the line he marks is not the line a
    finding sits on. rewrap.py records where each reflowed line came from, and
    a mark has to be carried back through that record before anything is
    compared. Getting this wrong would move every stop by a line or two, which
    would look like noise rather than like a bug."""

    def test_a_mark_is_carried_back_to_every_line_it_covers(self):
        # Reflowed line 5 was built from source lines 7 and 8.
        line_map = {5: [7, 8], 6: [8]}
        self.assertEqual(score.translate({5}, line_map), {7, 8})

    def test_marks_on_several_lines_are_unioned(self):
        line_map = {1: [1], 2: [2, 3], 3: [4]}
        self.assertEqual(score.translate({1, 3}, line_map), {1, 4})

    def test_a_mark_on_a_line_the_map_does_not_know_is_kept_as_itself(self):
        """Better to carry an unknown mark forward, where it shows up as a
        stop at no location, than to drop it silently."""
        self.assertEqual(score.translate({9}, {1: [1]}), {9})

    def test_no_map_leaves_the_marks_alone(self):
        self.assertEqual(score.translate({3, 4}, None), {3, 4})


if __name__ == "__main__":
    unittest.main()
