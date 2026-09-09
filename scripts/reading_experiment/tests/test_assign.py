"""Tests for assign.py, written before it exists.

The experiment: several checks read one draft and propose changes. A coin
decides which proposals go into the text Jake reads. He reads once, marking
where he stops. Then we compare how often he stopped where a change was made
against where one was not.

What has to be true for that comparison to mean anything, and what each test
below pins down:

1. The coin is the only thing that decides which proposals are applied, and
   the same seed gives the same coins, so the assignment can be reproduced
   from the record months later.
2. Assignment happens BEFORE anyone looks at the text, and the assignment file
   is written before the reading copy. Reversing that order would let the
   applying session see which locations matter.
3. Every proposal appears in the assignment exactly once, applied or held, so
   no proposal quietly disappears and no location is counted twice.
4. Applying a change alters the text at that location and nowhere else. A fix
   that shifts other line numbers would break the join between his marked
   stops and the locations.
5. The reading copy carries no mark saying which locations were changed. He
   must not be able to tell, or he is no longer reading as a reader.

Stdlib only, offline.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import assign  # noqa: E402


DRAFT = """The first line is plain.
A load-bearing assumption sits here.
This line has do both in it.
Nothing wrong with this one.
The registry holds the entries.
"""

FINDINGS = [
    {"id": "f1", "line": 2, "quote": "load-bearing assumption",
     "replacement": "assumption that Section 4 depends on", "check": "scanner"},
    {"id": "f2", "line": 3, "quote": "do both",
     "replacement": "run both checks", "check": "questions"},
    {"id": "f3", "line": 5, "quote": "The registry holds",
     "replacement": "The list of entries holds", "check": "questions"},
]


class SeedTest(unittest.TestCase):
    def test_same_seed_gives_the_same_assignment(self):
        a = assign.assign_findings(FINDINGS, seed=7)
        b = assign.assign_findings(FINDINGS, seed=7)
        self.assertEqual(a, b)

    def test_different_seeds_can_differ(self):
        """Not a guarantee for any one seed, so scan several."""
        base = assign.assign_findings(FINDINGS, seed=7)
        self.assertTrue(any(assign.assign_findings(FINDINGS, seed=s) != base
                            for s in range(1, 40)))

    def test_every_finding_is_assigned_exactly_once(self):
        out = assign.assign_findings(FINDINGS, seed=3)
        self.assertEqual(sorted(r["id"] for r in out), ["f1", "f2", "f3"])
        for row in out:
            self.assertIn(row["arm"], ("applied", "held"))

    def test_both_arms_occur_over_many_seeds(self):
        """A coin that always lands one way is not a coin."""
        arms = set()
        for s in range(50):
            for row in assign.assign_findings(FINDINGS, seed=s):
                arms.add(row["arm"])
        self.assertEqual(arms, {"applied", "held"})


class ApplyTest(unittest.TestCase):
    def test_applied_findings_change_their_own_line_only(self):
        rows = [dict(f, arm=("applied" if f["id"] == "f2" else "held"))
                for f in FINDINGS]
        out = assign.apply_findings(DRAFT, rows)
        before, after = DRAFT.split("\n"), out.split("\n")
        self.assertEqual(len(before), len(after), "line count must not change")
        self.assertNotEqual(before[2], after[2])
        for i in (0, 1, 3, 4):
            self.assertEqual(before[i], after[i], "line %d changed" % (i + 1))

    def test_held_findings_leave_the_text_alone(self):
        rows = [dict(f, arm="held") for f in FINDINGS]
        self.assertEqual(assign.apply_findings(DRAFT, rows), DRAFT)

    def test_the_replacement_text_is_what_lands(self):
        rows = [dict(f, arm=("applied" if f["id"] == "f1" else "held"))
                for f in FINDINGS]
        out = assign.apply_findings(DRAFT, rows)
        self.assertIn("assumption that Section 4 depends on", out)
        self.assertNotIn("load-bearing", out)

    def test_a_quote_that_is_not_there_is_an_error_not_a_silent_skip(self):
        rows = [{"id": "x", "line": 1, "quote": "not in the draft",
                 "replacement": "y", "check": "c", "arm": "applied"}]
        with self.assertRaises(ValueError):
            assign.apply_findings(DRAFT, rows)

    def test_the_reading_copy_carries_no_mark_of_which_lines_changed(self):
        rows = assign.assign_findings(FINDINGS, seed=11)
        out = assign.apply_findings(DRAFT, rows)
        for token in ("applied", "held", "arm", "f1", "f2", "f3", "<<", ">>"):
            self.assertNotIn(token, out)


class OrderTest(unittest.TestCase):
    def test_assignment_file_is_written_before_the_reading_copy(self):
        """Whoever applies the changes must not be able to choose them."""
        with tempfile.TemporaryDirectory() as d:
            draft = os.path.join(d, "draft.md")
            with open(draft, "w") as fh:
                fh.write(DRAFT)
            paths = assign.run(draft, FINDINGS, seed=5, out_dir=d)
            self.assertTrue(os.path.exists(paths["assignment"]))
            self.assertTrue(os.path.exists(paths["reading_copy"]))
            self.assertLessEqual(os.path.getmtime(paths["assignment"]),
                                 os.path.getmtime(paths["reading_copy"]))

    def test_the_assignment_file_records_the_seed_and_the_draft_hash(self):
        with tempfile.TemporaryDirectory() as d:
            draft = os.path.join(d, "draft.md")
            with open(draft, "w") as fh:
                fh.write(DRAFT)
            paths = assign.run(draft, FINDINGS, seed=5, out_dir=d)
            rec = json.load(open(paths["assignment"]))
            self.assertEqual(rec["seed"], 5)
            self.assertEqual(len(rec["draft_sha256"]), 64)
            self.assertEqual(len(rec["rows"]), 3)


if __name__ == "__main__":
    unittest.main()
