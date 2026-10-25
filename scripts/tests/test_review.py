"""Tests for scripts/review.py.

review.py holds the work Jake does for other people and for the institution
--- reviews, students' papers, letters, reimbursements, required trainings ---
apart from research. Each request is a folder holding REQUEST.md, a short
header followed by the steps for that kind of work, one per line as
`minutes | what to do`. Typing `review` shows one next action. The tests check
the decisions made on 2026-10-25:

- Order is earliest due date first, because the cost of this work is
  lateness to someone who is waiting, and earliest-due-first never makes the
  worst lateness larger than any other order does.
- A current step under 15 minutes goes first whatever its due date, so each
  reviewing slot can open with something finished, at a cost of only those
  minutes to the due-date order. A step of exactly 15 minutes does not.
- Every request gets a due date, written YYYY-MM-DD, when it is added; one
  without a date would sort last forever.
- The output is exactly one line in a fixed format and never mentions the
  other requests, because the count of waiting requests is what tells Jake he
  is behind. The fixed format also lets an agent read the line reliably.
- `done` closes the step `review` last showed, and refuses if the request at
  the front has changed since then, so it can never advance a request Jake
  has not seen.
- No step in the templates takes more than one 45-minute sitting, so the
  request at the front never reads as a whole review.
- The real folder sits in Dropbox among years of loose PDFs and folders that
  are not requests. Those are ignored. A request file the script cannot read
  produces an error naming it, never the empty-queue message.

The test date is 2024-02-27, not the real date, so an implementation that
ignores --today and reads the clock fails.

Stdlib only, offline, Python 3.9 or later, matching the other suites here.
"""

import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(REPO, "scripts", "review.py")
REAL_TEMPLATES = os.path.join(REPO, "scripts", "review_templates.txt")
TODAY = "2024-02-27"
EMPTY = "nothing in the review queue"

def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


TEMPLATES = """\
journal:
  10 | download the PDF into this folder
  45 | read once, marking the PDF
  45 | write the report
  10 | submit the report
reimbursement:
  10 | put the receipts in this folder
  30 | enter the expense report
training:
  15 | find the course link
  45 | do the training
"""


class ReviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # A space and an ampersand in the path catch code that moves folders
        # through a shell command without quoting.
        self.dir = os.path.join(self.tmp, "Dropbox & Co", "QUEUE")
        os.makedirs(self.dir)
        self.templates = os.path.join(self.tmp, "templates.txt")
        with open(self.templates, "w") as fh:
            fh.write(TEMPLATES)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # --- helpers

    def review(self, *args, ok=True):
        out = subprocess.run([sys.executable, SCRIPT, "--dir", self.dir, "--today", TODAY,
                              "--templates", self.templates, *args],
                             capture_output=True, text=True)
        if ok:
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(out.stderr, "")
        self.assertNotIn("Traceback", out.stderr)
        return out

    def add(self, title, kind="journal", due="2024-04-01"):
        return self.review("add", title, "--kind", kind, "--due", due)

    def request_files(self, where=None):
        return glob.glob(os.path.join(where or self.dir, "*", "REQUEST.md"))

    def request_file(self, title):
        found = [p for p in self.request_files() if f"title: {title}\n" in read(p)]
        self.assertEqual(len(found), 1, f"expected one request titled {title}")
        return found[0]

    def step_of(self, title):
        return int(re.search(r"(?m)^step: (\d+)$", read(self.request_file(title))).group(1))

    def set_step(self, title, step):
        # The header is plain text so Jake can edit it by hand; the tests
        # edit it the same way.
        path = self.request_file(title)
        text = re.sub(r"(?m)^step: \d+$", f"step: {step}", read(path))
        with open(path, "w") as fh:
            fh.write(text)

    def next_line(self):
        out = self.review().stdout
        lines = out.splitlines()
        self.assertEqual(len(lines), 1, out)
        return lines[0]

    def assert_nothing_written(self):
        self.assertEqual(os.listdir(self.dir), [])

    # --- adding

    def test_add_writes_header_and_template_steps(self):
        self.add("AJPS 2024-0412")
        text = read(self.request_file("AJPS 2024-0412"))
        for line in ("kind: journal", "due: 2024-04-01", f"added: {TODAY}", "step: 1"):
            self.assertIn(line + "\n", text)
        self.assertIn("45 | read once, marking the PDF", text)
        self.assertIn("10 | submit the report", text)

    def test_add_without_due_date_fails_and_writes_nothing(self):
        out = self.review("add", "No date", "--kind", "journal", ok=False)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("--due", out.stderr)
        self.assert_nothing_written()

    def test_add_with_unknown_kind_fails_and_writes_nothing(self):
        out = self.review("add", "Mystery", "--kind", "haiku", "--due", "2024-04-01", ok=False)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("haiku", out.stderr)
        self.assert_nothing_written()

    def test_add_with_malformed_due_date_fails_and_writes_nothing(self):
        # Python 3.11 reads "20240401" as a date and 3.10 does not, so the
        # script must insist on YYYY-MM-DD itself.
        for bad in ("2024-4-1", "20240401", "soon"):
            with self.subTest(due=bad):
                out = self.review("add", "Bad date", "--kind", "journal", "--due", bad, ok=False)
                self.assertNotEqual(out.returncode, 0)
                self.assertIn(bad, out.stderr)
                self.assert_nothing_written()

    def test_title_with_a_slash_is_found_again(self):
        self.add("Smith/Jones R&R")
        self.assertEqual(len(self.request_files()), 1)
        self.assertTrue(self.next_line().startswith("Smith/Jones R&R | "))

    def test_repeated_title_keeps_the_first_requests_progress(self):
        # A revise-and-resubmit often arrives under the same manuscript ID.
        self.add("AJPS 2024-0412", due="2024-03-15")
        self.review()
        self.review("done")
        self.add("AJPS 2024-0412", due="2024-05-01")
        files = self.request_files()
        self.assertEqual(len(files), 2)
        steps = sorted(int(re.search(r"(?m)^step: (\d+)$", read(p)).group(1)) for p in files)
        self.assertEqual(steps, [1, 2])

    # --- what `review` shows

    def test_shows_the_exact_line(self):
        self.add("AJPS 2024-0412")
        self.assertEqual(self.next_line(),
                         "AJPS 2024-0412 | due 2024-04-01 | 10 min | download the PDF into this folder")

    def test_earliest_due_date_first(self):
        self.add("Later", due="2024-04-20")
        self.add("Sooner", due="2024-03-10")
        # Move both to a 45-minute step so the short-step rule does not apply.
        self.set_step("Later", 2)
        self.set_step("Sooner", 2)
        self.assertTrue(self.next_line().startswith("Sooner | "))

    def test_due_date_beats_a_shorter_long_step(self):
        # Catches an implementation that sorts by minutes first: 30 minutes
        # is not a short step, so the earlier due date wins.
        self.add("Thirty minutes, later", kind="reimbursement", due="2024-04-30")
        self.set_step("Thirty minutes, later", 2)
        self.add("Forty-five minutes, sooner", due="2024-03-05")
        self.set_step("Forty-five minutes, sooner", 2)
        self.assertTrue(self.next_line().startswith("Forty-five minutes, sooner | "))

    def test_step_under_15_minutes_goes_first_whatever_its_due_date(self):
        self.add("Due soon, long step", due="2024-03-01")
        self.set_step("Due soon, long step", 2)   # 45 minutes
        self.add("Due later, short step", kind="reimbursement", due="2024-04-30")   # step 1: 10 minutes
        self.assertTrue(self.next_line().startswith("Due later, short step | "))

    def test_15_minute_step_does_not_jump_the_queue(self):
        self.add("Due soon, long step", due="2024-03-01")
        self.set_step("Due soon, long step", 2)   # 45 minutes
        self.add("Training, 15 minutes", kind="training", due="2024-04-30")
        self.assertTrue(self.next_line().startswith("Due soon, long step | "))

    def test_among_short_steps_earliest_due_first(self):
        self.add("Short, later", kind="reimbursement", due="2024-04-30")
        self.add("Short, sooner", kind="reimbursement", due="2024-03-15")
        self.assertTrue(self.next_line().startswith("Short, sooner | "))

    def test_never_mentions_the_other_requests(self):
        # Comparing the whole line also rules out a count such as "(4 more)".
        for i in range(5):
            self.add(f"Request {i}", due=f"2024-03-{10 + i}")
        self.assertEqual(self.next_line(),
                         "Request 0 | due 2024-03-10 | 10 min | download the PDF into this folder")

    def test_empty_queue_says_so(self):
        self.assertEqual(self.next_line().lower(), EMPTY)

    def test_clutter_is_ignored(self):
        for name in ("notes.docx", "paper.pdf", ".DS_Store", "Icon\r"):
            open(os.path.join(self.dir, name), "w").close()
        os.makedirs(os.path.join(self.dir, "old-review-folder"))
        open(os.path.join(self.dir, "old-review-folder", "manuscript.pdf"), "w").close()
        with self.subTest("clutter alone"):
            self.assertEqual(self.next_line().lower(), EMPTY)
        self.add("Real request")
        # Dropbox writes a conflicted copy beside the file it could not merge.
        folder = os.path.dirname(self.request_file("Real request"))
        with open(os.path.join(folder, "REQUEST (Jake's conflicted copy 2024-02-20).md"), "w") as fh:
            fh.write("garbage\n")
        with self.subTest("clutter and one request"):
            self.assertTrue(self.next_line().startswith("Real request | "))

    def test_archived_requests_are_never_shown(self):
        old = os.path.join(self.dir, "Archive", "old-review")
        os.makedirs(old)
        with open(os.path.join(old, "REQUEST.md"), "w") as fh:
            fh.write("---\ntitle: Old\nkind: journal\ndue: 2024-01-01\nadded: 2023-12-01\nstep: 1\n---\n"
                     "10 | submit the report\n")
        self.assertEqual(self.next_line().lower(), EMPTY)

    def test_broken_request_is_an_error_not_an_empty_queue(self):
        broken = {
            "no-header": "no header here\n",
            "step-past-end": "---\ntitle: X\nkind: journal\ndue: 2024-04-01\nadded: 2024-02-01\nstep: 9\n---\n"
                             "10 | only step\n",
            "due-not-a-date": "---\ntitle: Y\nkind: journal\ndue: soon\nadded: 2024-02-01\nstep: 1\n---\n"
                              "10 | only step\n",
        }
        for name, text in broken.items():
            with self.subTest(name):
                folder = os.path.join(self.dir, name)
                os.makedirs(folder)
                with open(os.path.join(folder, "REQUEST.md"), "w") as fh:
                    fh.write(text)
                out = self.review(ok=False)
                self.assertNotEqual(out.returncode, 0)
                self.assertIn(name, out.stderr)
                self.assertNotIn(EMPTY, (out.stdout + out.stderr).lower())
                shutil.rmtree(folder)

    # --- finishing steps

    def test_done_closes_the_step_just_shown(self):
        self.add("AJPS 2024-0412")
        self.review()
        out = self.review("done").stdout.splitlines()
        self.assertEqual(len(out), 1)
        self.assertIn("AJPS 2024-0412", out[0])
        self.assertIn("download the PDF into this folder", out[0])
        self.assertIn("read once, marking the PDF", self.next_line())

    def test_done_without_review_first_refuses_and_changes_nothing(self):
        self.add("AJPS 2024-0412")
        out = self.review("done", ok=False)
        self.assertNotEqual(out.returncode, 0)
        self.assertEqual(self.step_of("AJPS 2024-0412"), 1)

    def test_done_refuses_when_the_front_changed_since_review(self):
        self.add("Shown", due="2024-03-01")
        self.set_step("Shown", 2)   # 45 minutes
        self.review()               # shows "Shown"
        # A short step added afterward moves to the front.
        self.add("Arrived later", kind="reimbursement", due="2024-04-30")
        out = self.review("done", ok=False)
        self.assertNotEqual(out.returncode, 0)
        self.assertEqual(self.step_of("Shown"), 2)
        self.assertEqual(self.step_of("Arrived later"), 1)

    def test_done_tells_two_requests_with_the_same_title_apart(self):
        # The record of what was shown has to name the folder, not the title.
        self.add("Trip", due="2024-03-01")
        self.set_step("Trip", 2)    # 45 minutes
        self.review()               # shows this "Trip"
        self.add("Trip", kind="reimbursement", due="2024-04-30")   # 10 minutes, moves to the front
        out = self.review("done", ok=False)
        self.assertNotEqual(out.returncode, 0)
        steps = sorted(int(re.search(r"(?m)^step: (\d+)$", read(p)).group(1)) for p in self.request_files())
        self.assertEqual(steps, [1, 2])

    def test_done_still_works_after_an_add_that_leaves_the_front_alone(self):
        self.add("Front", kind="reimbursement", due="2024-03-01")
        self.review()
        self.add("Behind", due="2024-04-30")
        self.set_step("Behind", 2)   # 45 minutes, due later: stays behind
        self.review("done")
        self.assertEqual(self.step_of("Front"), 2)
        self.assertEqual(self.step_of("Behind"), 2)

    def test_done_twice_after_one_review_refuses_the_second(self):
        self.add("AJPS 2024-0412")
        self.review()
        self.review("done")
        out = self.review("done", ok=False)
        self.assertNotEqual(out.returncode, 0)
        self.assertEqual(self.step_of("AJPS 2024-0412"), 2)

    def test_done_on_empty_queue_refuses_and_creates_nothing(self):
        out = self.review("done", ok=False)
        self.assertNotEqual(out.returncode, 0)
        # The message, not just the exit code, so a missing script cannot pass.
        self.assertIn(EMPTY, out.stderr.lower())
        self.assert_nothing_written()

    def test_done_on_last_step_archives_the_request(self):
        self.add("Conference trip", kind="reimbursement")
        for _ in range(2):
            self.review()
            self.review("done")
        self.assertEqual(len(self.request_files(os.path.join(self.dir, "Archive"))), 1)
        self.assertEqual(self.request_files(), [])
        self.assertEqual(self.next_line().lower(), EMPTY)

    def test_archiving_two_requests_with_the_same_title_keeps_both(self):
        for due in ("2024-03-01", "2024-04-01"):
            self.add("Trip", kind="reimbursement", due=due)
            for _ in range(2):
                self.review()
                self.review("done")
        archive = os.path.join(self.dir, "Archive")
        self.assertEqual(len(self.request_files(archive)), 2)
        self.assertEqual(glob.glob(os.path.join(archive, "*", "*", "REQUEST.md")), [])

    # --- Jake's real templates

    def test_the_real_templates_work_for_every_kind(self):
        self.templates = REAL_TEMPLATES
        for kind in ("journal", "student-paper", "letter", "reimbursement", "training"):
            self.add(f"A {kind} request", kind=kind)
        self.assertEqual(len(self.request_files()), 5)

    def test_every_real_template_step_fits_one_sitting(self):
        kinds, minutes = set(), []
        for line in read(REAL_TEMPLATES).splitlines(True):
            if not line.strip():
                continue
            if re.match(r"^\S.*:\s*$", line):
                kinds.add(line.strip().rstrip(":"))
                continue
            m = re.match(r"^\s+(\d+) \| \S", line)
            self.assertIsNotNone(m, f"step line not in 'minutes | text' form: {line!r}")
            minutes.append(int(m.group(1)))
        self.assertTrue({"journal", "student-paper", "letter", "reimbursement", "training"} <= kinds, kinds)
        self.assertTrue(minutes)
        self.assertLessEqual(max(minutes), 45)


if __name__ == "__main__":
    unittest.main()
