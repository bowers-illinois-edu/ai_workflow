#!/usr/bin/env python3
"""Tests that style_gate.py never passes a mail file to the reader or to Claude.

Why this exists. Since 2026-10-25 Jake's mail extractor lives in its own
repository, ~/repos/mail-extract, and sessions started there run inside
Claude Code's sandbox, which blocks ~/Library/Thunderbird (Thunderbird's
copy of his mail) and ~/mail-extract-output (the extractor's output) at the
operating-system level. The reply check, `style_gate.py check`, cannot run
inside the sandbox, because it starts `claude -p`, which writes under
~/.claude. So the check will be listed as a command that runs outside the
sandbox. Run that way, it can open any file, and it does two things with the
file it is given:

  * it sends the file's text to a second model, the reader, and
  * it prints the scanner's matches, which quote words from the file, to
    the shell that Claude reads.

Without a guard, a session could name a mail file as the draft and send the
mail out by either route. The rule Jake set for the extractor is that no AI
reads his mailbox, and Claude sees only the file Jake chooses to hand over.

What the tests require:

  * `check` refuses a draft, a `--transcript` file, or a `--point` file
    that lies under a private folder. A refusal calls no reader, runs no
    scan, and prints nothing from the file, only which argument was
    refused.
  * The test is made on the resolved path, so a symlink placed elsewhere
    that points into a private folder is refused, and so is a path that
    reaches one through "..". On a Mac disk, which ignores letter case, a
    path spelled in other case is refused too.
  * A folder whose name merely begins with a private folder's name is not
    private: ~/mail-extract-output-old is not ~/mail-extract-output.
  * The PostToolUse hook, which scans prose files a tool just wrote and
    injects its matches into Claude's context, skips files under a private
    folder in the same way.
  * Every path returns 0, like every other path through the gate.
  * By default the private folders are exactly the two named above.

Not covered: a hard link to a mail file has a path of its own that no
resolution traces back to the mail folder. Whether a sandboxed command can
make one is something the Claude Code documentation does not say.

The tests never touch the real mail folders. They point the gate's list of
private folders at temporary folders instead.

Run: python3 test_style_gate_private.py
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
import style_gate as sg  # noqa: E402

EM_DASH = "\u2014"

# A word that appears only inside the private files. If it shows up in
# anything the gate prints or sends to the reader, a mail file got out.
SECRET = "aardvarkcodeword"

# Mail-like text with a scanner hit in it, so that a scan of the file, had
# one run, would print a match quoting the file.
MAIL_TEXT = ("From: Jane <jane@example.org>\n\n"
             "The %s is due Friday %s please confirm.\n" % (SECRET, EM_DASH))


def posttool_event(tool_name, tool_input):
    """A PostToolUse event as the harness delivers it on stdin."""
    return json.dumps({"hook_event_name": "PostToolUse",
                       "session_id": "s1",
                       "tool_name": tool_name,
                       "tool_input": tool_input,
                       "tool_response": {}})


class PrivateCase(unittest.TestCase):
    """A temporary home holding two private folders and one ordinary one."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = self._tmp.name
        self.log = os.path.join(root, "logs", "style_gate.jsonl")
        self.mail = os.path.join(root, "Thunderbird")
        self.output = os.path.join(root, "mail-extract-output")
        self.public = os.path.join(root, "scratch")
        for d in (self.mail, self.output, self.public):
            os.makedirs(d)
        # getattr, so that before the guard exists each test still runs and
        # fails on what leaked rather than on the missing name.
        self._saved = getattr(sg, "PRIVATE_DIRS", None)
        sg.PRIVATE_DIRS = (self.mail, self.output)
        self.calls = []

    def tearDown(self):
        if self._saved is None:
            del sg.PRIVATE_DIRS
        else:
            sg.PRIVATE_DIRS = self._saved
        self._tmp.cleanup()

    def write(self, path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def reader(self, prompt):
        self.calls.append(prompt)
        return "[]"

    def check(self, draft, transcript=None, point=None):
        """Run `check` with the fake reader; return (code, output).

        run_check is called directly, because main would bind the real
        reader, which calls `claude -p`, and these tests stay offline. The
        guard belongs in run_check for the same reason: every path into the
        reader goes through it."""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.run_check(draft, self.log, transcript, self.reader,
                                point_path=point)
        return code, buf.getvalue()

    def assertRefusedWithoutLeaking(self, code, out):
        self.assertEqual(code, 0)
        self.assertEqual(self.calls, [], "the reader was called")
        self.assertNotIn(SECRET, out)
        self.assertNotIn("U+2014", out, "the scanner ran on the private file")
        self.assertIn("refused", out.lower())


class TestDefaultPrivateFolders(unittest.TestCase):

    def test_the_two_mail_folders_are_private_by_default(self):
        # Compared as strings only; nothing here opens the real folders.
        expected = {os.path.expanduser("~/Library/Thunderbird"),
                    os.path.expanduser("~/mail-extract-output")}
        self.assertEqual(set(sg.PRIVATE_DIRS), expected)


class TestCheckRefusesPrivateFiles(PrivateCase):

    def test_a_draft_inside_the_mail_folder_is_refused(self):
        path = self.write(os.path.join(self.mail, "INBOX"), MAIL_TEXT)
        self.assertRefusedWithoutLeaking(*self.check(path))

    def test_a_draft_deep_inside_the_output_folder_is_refused(self):
        path = self.write(os.path.join(self.output, "2026", "mail.jsonl"), MAIL_TEXT)
        self.assertRefusedWithoutLeaking(*self.check(path))

    def test_a_symlink_elsewhere_pointing_into_the_mail_folder_is_refused(self):
        # A sandboxed command cannot read the mail, but it can make a link
        # to it; the check, running outside the sandbox, would follow it.
        target = self.write(os.path.join(self.mail, "INBOX"), MAIL_TEXT)
        link = os.path.join(self.public, "draft.md")
        os.symlink(target, link)
        self.assertRefusedWithoutLeaking(*self.check(link))

    def test_a_path_that_climbs_into_the_mail_folder_is_refused(self):
        self.write(os.path.join(self.mail, "INBOX"), MAIL_TEXT)
        sneaky = os.path.join(self.public, "..", "Thunderbird", "INBOX")
        self.assertRefusedWithoutLeaking(*self.check(sneaky))

    def test_a_path_spelled_in_other_letter_case_is_refused(self):
        # A Mac disk ignores letter case, and os.path.realpath keeps the case
        # it was given, so a comparison of spellings would let this through.
        self.write(os.path.join(self.mail, "INBOX"), MAIL_TEXT)
        variant = os.path.join(os.path.dirname(self.mail), "THUNDERBIRD", "INBOX")
        if not os.path.exists(variant):
            self.skipTest("this disk distinguishes letter case")
        self.assertRefusedWithoutLeaking(*self.check(variant))

    def test_a_point_file_inside_the_mail_folder_is_refused(self):
        # read_point sends up to POINT_CHARS of this file to the reader.
        draft = self.write(os.path.join(self.public, "draft.md"), "A plain reply.\n")
        point = self.write(os.path.join(self.mail, "INBOX"), MAIL_TEXT)
        code, out = self.check(draft, point=point)
        self.assertRefusedWithoutLeaking(code, out)
        self.assertIn("--point", out)

    def test_a_transcript_inside_the_output_folder_is_refused(self):
        draft = self.write(os.path.join(self.public, "draft.md"), "A plain reply.\n")
        transcript = self.write(os.path.join(self.output, "mail.jsonl"), MAIL_TEXT)
        code, out = self.check(draft, transcript=transcript)
        self.assertRefusedWithoutLeaking(code, out)
        self.assertIn("--transcript", out)

    def test_a_folder_that_only_shares_the_prefix_is_not_private(self):
        # "mail-extract-output-old" begins with "mail-extract-output" but is
        # a different folder, so a draft there is checked as usual.
        sibling = self.output + "-old"
        path = self.write(os.path.join(sibling, "draft.md"), "A plain reply.\n")
        code, out = self.check(path)
        self.assertEqual(code, 0)
        self.assertEqual(len(self.calls), 1)
        self.assertNotIn("refused", out.lower())

    def test_an_ordinary_draft_still_reaches_the_reader(self):
        path = self.write(os.path.join(self.public, "draft.md"), "A plain reply.\n")
        code, out = self.check(path)
        self.assertEqual(code, 0)
        self.assertEqual(len(self.calls), 1)
        self.assertIn("A plain reply.", self.calls[0])


class TestPostToolSkipsPrivateFiles(PrivateCase):
    """The PostToolUse hook injects the scanner's matches into Claude's
    context, and those matches quote the file, so it must not scan a private
    file either."""

    def posttool(self, tool_name, tool_input):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], posttool_event(tool_name, tool_input),
                           self.log)
        return code, buf.getvalue()

    def test_a_write_to_a_prose_file_in_the_mail_folder_is_not_scanned(self):
        path = self.write(os.path.join(self.mail, "notes.md"), MAIL_TEXT)
        code, out = self.posttool("Write", {"file_path": path})
        self.assertEqual(code, 0)
        self.assertNotIn(SECRET, out)
        self.assertEqual(out.strip(), "")

    def test_a_prose_named_symlink_into_the_mail_folder_is_not_scanned(self):
        target = self.write(os.path.join(self.mail, "INBOX"), MAIL_TEXT)
        link = os.path.join(self.public, "inbox.md")
        os.symlink(target, link)
        code, out = self.posttool("Edit", {"file_path": link})
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "")

    def test_a_bash_command_naming_a_private_prose_file_is_not_scanned(self):
        path = self.write(os.path.join(self.output, "summary.md"), MAIL_TEXT)
        code, out = self.posttool("Bash", {"command": "touch %s" % path})
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "")

    def test_an_ordinary_prose_file_is_still_scanned(self):
        path = self.write(os.path.join(self.public, "memo.md"),
                          "The estimand %s not the estimate.\n" % EM_DASH)
        _, out = self.posttool("Write", {"file_path": path})
        self.assertIn("memo.md", out)


if __name__ == "__main__":
    unittest.main()
