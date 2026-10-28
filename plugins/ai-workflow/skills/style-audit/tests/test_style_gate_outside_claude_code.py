#!/usr/bin/env python3
"""Tests that `style_gate.py check` calls no cloud model outside Claude Code.

Why this exists. The reply check, `style_gate.py check`, runs the scanner
and then a second reader, Claude Sonnet, which it starts with `claude -p`.
Claude Sonnet runs on Anthropic's servers. On 2026-10-28 we found that the
Lumen models Jake runs in OpenCode follow the rule in AGENTS.md and run the
check, 59 times between 2026-10-05 and 2026-10-28, and that 58 of those runs
reached the reader. So 58 drafts written by Lumen models went to Anthropic.
Jake's rule, the same day: an open-weight model must not call a model that
runs in the cloud. A Lumen model may call only models on the university's
servers.

The reader was also wrong outside Claude Code. It is meant to read the draft
beside Jake's recent messages, and the script finds those in Claude Code's
transcripts under ~/.claude/projects/. OpenCode writes no such transcript,
so the reader got the newest Claude Code transcript for the folder, which
belongs to another session. In 530-grading on 2026-10-27, ten of its eleven
reports said Jake had never asked the question he had asked.

Jake chose on 2026-10-28 that outside Claude Code the check runs the
scanner only (memo_opencode_materials_2026-10-28.md, decision 2).

What the tests require:

  * Outside Claude Code, `check` starts no process at all, so it cannot
    start `claude`. That holds when a --transcript file is named too,
    because the rule is about where the draft goes, not about which
    conversation the reader would see.
  * Outside Claude Code, it reads no Claude Code transcript, because the
    transcript it would find belongs to another session.
  * The scanner still runs and prints its findings.
  * The output says the second reader was skipped and why, so a model
    reading it does not take the silence for a clean draft. It never prints
    "Nothing found by the scanner or the reader", which would claim a
    reading that did not happen.
  * Inside Claude Code the reader is still called, as before.
  * "Inside Claude Code" means the shell has CLAUDECODE=1, which Claude
    Code sets in every shell it starts. OpenCode's background server, as
    started on Jake's laptop, carries no CLAUDE variable (checked
    2026-10-28 with `ps eww`).

Not covered: an OpenCode started from a shell that Claude Code itself
started would inherit CLAUDECODE=1, and its checks would reach the reader.
Jake starts OpenCode in a Ghostty tab, not from Claude Code.

The tests stay offline. subprocess.Popen is replaced with a stand-in that
records every command and starts nothing.

Run: python3 test_style_gate_outside_claude_code.py
"""

import contextlib
import io
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
import style_gate as sg  # noqa: E402

EM_DASH = "—"


class RecordingPopen:
    """Stands in for subprocess.Popen: records the command, starts nothing,
    and answers as a reader that found nothing would."""

    commands = []

    def __init__(self, cmd, *args, **kwargs):
        RecordingPopen.commands.append(list(cmd))
        self.pid = 0
        self.returncode = 0

    def communicate(self, *args, **kwargs):
        return ("[]", "")


class OutsideCase(unittest.TestCase):
    """A temporary draft and log, and a shell environment with or without
    Claude Code's mark."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.log = os.path.join(self._tmp.name, "logs", "style_gate.jsonl")
        RecordingPopen.commands = []
        self.transcripts_read = []

    def tearDown(self):
        self._tmp.cleanup()

    def draft(self, text):
        path = os.path.join(self._tmp.name, "draft.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def transcript(self):
        """A Claude Code transcript from some other session."""
        path = os.path.join(self._tmp.name, "other_session.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{}\n")
        return path

    def record_visible_turns(self, path, *args, **kwargs):
        self.transcripts_read.append(path)
        return []

    def run_main(self, argv, claude_code):
        """Run `check` through main, as the shell runs it, with CLAUDECODE
        set or removed. Returns (code, output)."""
        env = dict(os.environ)
        env.pop("CLAUDECODE", None)
        if claude_code:
            env["CLAUDECODE"] = "1"
        buf = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(sg.subprocess, "Popen", RecordingPopen), \
                mock.patch.object(sg, "visible_turns",
                                  self.record_visible_turns), \
                mock.patch.object(sg, "newest_transcript",
                                  lambda *a, **k: self.transcript()), \
                contextlib.redirect_stdout(buf):
            code = sg.main(argv, "", self.log)
        return code, buf.getvalue()


class TestOutsideClaudeCodeNoCloudModel(OutsideCase):

    def test_no_process_is_started(self):
        """The rule itself: no `claude`, and no other program either."""
        code, _out = self.run_main(["check", self.draft("Plain text.\n")],
                                   claude_code=False)
        self.assertEqual(code, 0)
        self.assertEqual(RecordingPopen.commands, [])

    def test_no_process_is_started_when_a_transcript_is_named(self):
        """Naming the conversation does not make sending the draft to
        Anthropic allowed."""
        argv = ["check", self.draft("Plain text.\n"),
                "--transcript", self.transcript()]
        self.run_main(argv, claude_code=False)
        self.assertEqual(RecordingPopen.commands, [])

    def test_no_claude_code_transcript_is_read(self):
        """The newest transcript in the folder belongs to another session."""
        self.run_main(["check", self.draft("Plain text.\n")],
                      claude_code=False)
        self.assertEqual(self.transcripts_read, [])


class TestOutsideClaudeCodeOutput(OutsideCase):

    def test_scanner_findings_are_still_printed(self):
        path = self.draft("The estimand %s the estimate.\n" % EM_DASH)
        code, out = self.run_main(["check", path], claude_code=False)
        self.assertEqual(code, 0)
        self.assertIn("U+2014", out)

    def test_output_says_the_reader_was_skipped(self):
        _code, out = self.run_main(["check", self.draft("Plain text.\n")],
                                   claude_code=False)
        self.assertIn("Reader skipped", out)
        self.assertIn("Claude Code", out)

    def test_a_clean_draft_does_not_claim_a_reading(self):
        """Without the reader, a clean scan is all that can be said."""
        _code, out = self.run_main(["check", self.draft("Plain text.\n")],
                                   claude_code=False)
        self.assertNotIn("Nothing found by the scanner or the reader", out)
        self.assertIn("Scanner: nothing found.", out)


class TestInsideClaudeCodeNothingChanges(OutsideCase):

    def test_the_reader_is_still_started(self):
        self.run_main(["check", self.draft("Plain text.\n")],
                      claude_code=True)
        self.assertEqual(len(RecordingPopen.commands), 1)
        self.assertEqual(RecordingPopen.commands[0][:2], ["claude", "-p"])

    def test_the_transcript_is_still_read(self):
        self.run_main(["check", self.draft("Plain text.\n")],
                      claude_code=True)
        self.assertEqual(len(self.transcripts_read), 1)


class TestWhatCountsAsClaudeCode(unittest.TestCase):
    """Only Claude Code's own mark counts. A variable some other tool sets,
    or a stray CLAUDE_CODE_SESSION_ID without the mark, does not."""

    def test_the_mark(self):
        self.assertTrue(sg.in_claude_code({"CLAUDECODE": "1"}))

    def test_no_mark(self):
        self.assertFalse(sg.in_claude_code({}))
        self.assertFalse(sg.in_claude_code({"OPENCODE": "1"}))
        self.assertFalse(sg.in_claude_code({"CLAUDE_CODE_SESSION_ID": "abc"}))
        self.assertFalse(sg.in_claude_code({"CLAUDECODE": "0"}))


if __name__ == "__main__":
    unittest.main()
