"""Tests for the Obsidian note that review.py keeps, written before the code.

Jake reads notes in Obsidian on his iPhone, iPad, and MacBook, and the
Dropbox app is no good for reading anything but PDFs, so the review queue
has to be visible in Obsidian to be visible away from the Mac. On
2026-10-25 he asked to "see what I have to do at a glance with the next one
on top and clearly marked", and said that one note per request would itself
feel overwhelming. So review.py keeps one note, in the vault that Obsidian
Sync copies to his devices, listing every request in the queue.

The tests check the decisions that follow:

- The note lists the requests in the order `review` would show them, so the
  request under "Next" is the one `review` prints, word for word, and the
  others follow in order under "After that".
- review.py rewrites the note after `review`, `review add`, and `review
  done`, so the note never shows a step that has been closed.
- `review` itself still prints one line and nothing about the other
  requests (test_review.py), because the note is the only place Jake chose
  to see the whole list.
- An empty queue gives a note saying so. A REQUEST.md that cannot be read is
  an error and leaves the note as it was, so the note never claims an empty
  queue while a request is broken.
- A missing vault folder does not stop review.py from doing its work; it
  says once, on stderr, that the note was not written.
- By default the note is review_queue.md at the top of ~/Documents/Obsidian
  Vault. Jake asked on 2026-10-25 for a name without spaces.

The test date is 2024-02-27, as in test_review.py. Every run passes --note
pointing at a temporary folder, so no test writes the real vault.

Stdlib only, offline, Python 3.9 or later.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(REPO, "review", "review.py")
TODAY = "2024-02-27"
EMPTY = "nothing in the review queue"

TEMPLATES = """\
journal:
  10 | download the PDF into this folder
  45 | read once, marking the PDF
  45 | write the report
  10 | submit the report
reimbursement:
  10 | put the receipts in this folder
  30 | enter the expense report
"""


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class NoteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.dir = os.path.join(self.tmp, "Dropbox", "QUEUE")
        os.makedirs(self.dir)
        self.vault = os.path.join(self.tmp, "Obsidian Vault")
        os.makedirs(self.vault)
        self.note = os.path.join(self.vault, "review_queue.md")
        self.templates = os.path.join(self.tmp, "templates.txt")
        with open(self.templates, "w") as fh:
            fh.write(TEMPLATES)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def review(self, *args, note=None, ok=True):
        out = subprocess.run([sys.executable, SCRIPT, "--dir", self.dir, "--today", TODAY,
                              "--templates", self.templates, "--note", note or self.note, *args],
                             capture_output=True, text=True)
        if ok:
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(out.stderr, "")
        self.assertNotIn("Traceback", out.stderr)
        return out

    def add(self, title, kind="journal", due="2024-04-01"):
        return self.review("add", title, "--kind", kind, "--due", due)

    def set_step(self, title, step):
        for name in os.listdir(self.dir):
            path = os.path.join(self.dir, name, "REQUEST.md")
            if os.path.isfile(path) and f"title: {title}\n" in read(path):
                # Read before opening for writing, which empties the file.
                text = re.sub(r"(?m)^step: \d+$", f"step: {step}", read(path))
                with open(path, "w") as fh:
                    fh.write(text)

    def sections(self):
        """The lines under the note's "Next" and "After that" headings.

        Blank lines and the list markers "1. ", "2. " are dropped, so the
        tests check what the note says, not how Markdown numbers a list."""
        text = read(self.note)
        found, current = {}, None
        for line in text.splitlines():
            heading = re.match(r"^#+\s*(.*?)\s*$", line)
            if heading:
                current = heading.group(1).lower()
                found[current] = []
            elif current and line.strip():
                found[current].append(re.sub(r"^\s*(\d+\.|[-*])\s+", "", line.strip()))
        return found

    def test_next_is_exactly_what_review_prints_and_the_rest_follow_in_order(self):
        # Three requests whose order needs both rules: the 10-minute step
        # goes first whatever its due date, then earliest due date.
        self.add("Due later, short step", kind="reimbursement", due="2024-04-30")
        self.add("Due soon, long step", due="2024-03-01")
        self.set_step("Due soon, long step", 2)
        self.add("Due last, long step", due="2024-05-15")
        self.set_step("Due last, long step", 2)
        printed = self.review().stdout.strip()
        found = self.sections()
        self.assertEqual(found["next"], [printed])
        self.assertEqual(found["after that"], [
            "Due soon, long step | due 2024-03-01 | 45 min | read once, marking the PDF",
            "Due last, long step | due 2024-05-15 | 45 min | read once, marking the PDF",
        ])

    def test_add_alone_updates_the_note(self):
        self.add("AJPS 2024-0412")
        self.assertEqual(self.sections()["next"],
                         ["AJPS 2024-0412 | due 2024-04-01 | 10 min | download the PDF into this folder"])

    def test_done_updates_the_note_so_a_closed_step_never_shows(self):
        self.add("AJPS 2024-0412")
        self.review()
        self.review("done")
        text = read(self.note)
        self.assertNotIn("download the PDF into this folder", text)
        self.assertIn("AJPS 2024-0412 | due 2024-04-01 | 45 min | read once, marking the PDF", text)

    def test_one_request_has_nothing_after_it(self):
        self.add("AJPS 2024-0412")
        self.assertEqual(self.sections().get("after that", []), [])

    def test_empty_queue_note_says_so(self):
        self.review()
        self.assertIn(EMPTY, read(self.note).lower())

    def test_archived_requests_are_not_in_the_note(self):
        self.add("Finished one", kind="reimbursement")
        self.set_step("Finished one", 2)
        self.review()
        self.review("done")   # last step, so the request moves to Archive
        self.add("Still open")
        text = read(self.note)
        self.assertNotIn("Finished one", text)
        self.assertIn("Still open", text)

    def test_broken_request_leaves_the_note_as_it_was(self):
        self.add("AJPS 2024-0412")
        before = read(self.note)
        folder = os.path.join(self.dir, "broken")
        os.makedirs(folder)
        with open(os.path.join(folder, "REQUEST.md"), "w") as fh:
            fh.write("no header here\n")
        out = self.review(ok=False)
        self.assertNotEqual(out.returncode, 0)
        self.assertEqual(read(self.note), before)

    def test_missing_vault_folder_does_not_stop_the_work(self):
        missing = os.path.join(self.tmp, "No Such Vault", "review_queue.md")
        out = self.review("add", "AJPS 2024-0412", "--kind", "journal", "--due", "2024-04-01",
                          note=missing, ok=False)
        self.assertEqual(out.returncode, 0)
        self.assertIn("added: AJPS 2024-0412", out.stdout)
        self.assertEqual(len(out.stderr.strip().splitlines()), 1, out.stderr)
        self.assertIn("note", out.stderr.lower())
        self.assertFalse(os.path.exists(os.path.dirname(missing)))

    def test_default_note_is_in_the_obsidian_vault(self):
        out = subprocess.run([sys.executable, SCRIPT, "--help"], capture_output=True, text=True)
        self.assertIn("Obsidian Vault/review_queue.md", " ".join(out.stdout.split()))


if __name__ == "__main__":
    unittest.main()
