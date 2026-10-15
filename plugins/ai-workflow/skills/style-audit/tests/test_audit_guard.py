#!/usr/bin/env python3
"""Unit tests for audit_guard.py, the Stop hook that keeps a turn from ending
while a document the assistant saved has not been through the style audit.

Why it exists. Jake, 2026-10-15: "I kind of hate having to constantly say
'did you do a full style-audit' and being told 'Oh no! I need to do it.
Please wait...'" The rules already told the assistant to audit every document
before reporting it done, and a PostToolUse note already reminded it after
every saved prose file. The same day the assistant saved a memo, ran only the
reply check on it, and reported it done. A reminder in front of the writer
does not make the writer audit. A Stop hook can refuse to let the turn end,
so the audit happens before Jake has to ask.

What the guard decides, and the tests below pin:

  * A DOCUMENT is a prose file (the suffixes style_gate.py scans) that the
    assistant saved since Jake's last message: with Write, Edit, MultiEdit,
    or a Bash command that names the file and left it modified after that
    message. Drafts in a temporary directory (the replies checked with
    `style_gate.py check`) and files under ~/.claude (memory, settings) are
    not documents.

  * A document is AUDITED when the style-audit skill, or both-passes, which
    runs it, was invoked after the document was first saved. Edits that
    apply the audit's fixes come after the audit, and they must not trigger
    a second round, which is why the first save is what counts.

  * The guard blocks at most once per stop. When Claude Code reports that the
    assistant is already continuing because of a Stop hook, the guard lets
    the turn end, so it can never loop.

  * It FAILS OPEN. A missing transcript, unreadable input, or any error lets
    the turn end silently, because a broken guard must not wedge a session.

Run: python3 test_audit_guard.py    (or via the repo-root Makefile: make test)
"""

import calendar
import contextlib
import io
import json
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
import audit_guard as ag  # noqa: E402

T0 = "2026-10-15T20:00:00.000Z"
T1 = "2026-10-15T20:01:00.000Z"
T2 = "2026-10-15T20:02:00.000Z"
T3 = "2026-10-15T20:03:00.000Z"
T4 = "2026-10-15T20:04:00.000Z"


def jake(text, ts):
    """Something Jake typed."""
    return {"type": "user", "timestamp": ts,
            "message": {"role": "user", "content": text}}


def injected(text, ts):
    """Text the harness put in a user record; Jake never typed it."""
    return {"type": "user", "timestamp": ts,
            "message": {"role": "user", "content": text}}


def tool_result(ts, use_id="x"):
    return {"type": "user", "timestamp": ts,
            "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": use_id,
                 "content": "ok"}]}}


def tool(name, tool_input, ts, cwd="/", use_id="x"):
    return {"type": "assistant", "timestamp": ts, "cwd": cwd,
            "message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": use_id, "name": name,
                 "input": tool_input}]}}


def write(path, ts):
    return tool("Write", {"file_path": path, "content": "x"}, ts)


def edit(path, ts):
    return tool("Edit", {"file_path": path, "old_string": "a",
                         "new_string": "b"}, ts)


def skill(name, ts, args=""):
    return tool("Skill", {"skill": name, "args": args}, ts)


class GuardCase(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        # The project and the home directory live under the test's own
        # temporary directory, which the guard would otherwise treat as a
        # scratch area. So the tests name the scratch roots explicitly.
        self.root = self._tmp.name
        self.home = os.path.join(self.root, "home")
        self.proj = os.path.join(self.root, "proj")
        self.scratch = os.path.join(self.root, "scratch")
        for d in (self.home, self.proj, self.scratch):
            os.makedirs(d)
        self.memo = os.path.join(self.proj, "memo.md")
        self.log = os.path.join(self.root, "logs", "audit_guard.jsonl")

    def tearDown(self):
        self._tmp.cleanup()

    def transcript(self, records):
        path = os.path.join(self.root, "t.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for r in records:
                fh.write(json.dumps(r) + "\n")
        return path

    def pending(self, records):
        return ag.unaudited_documents(self.transcript(records),
                                      home=self.home,
                                      scratch_roots=(self.scratch,))

    def run_hook(self, records, **event):
        payload = {"hook_event_name": "Stop", "session_id": "s1",
                   "transcript_path": self.transcript(records)}
        payload.update(event)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = ag.run(json.dumps(payload), self.log, home=self.home,
                          scratch_roots=(self.scratch,))
        out = buf.getvalue().strip()
        return code, (json.loads(out) if out else None)


class TestWhatCountsAsUnaudited(GuardCase):

    def test_a_memo_saved_and_never_audited_is_pending(self):
        recs = [jake("write the memo", T0), write(self.memo, T1)]
        self.assertEqual(self.pending(recs), [self.memo])

    def test_a_memo_audited_after_it_was_saved_is_not_pending(self):
        recs = [jake("write the memo", T0), write(self.memo, T1),
                skill("style-audit", T2)]
        self.assertEqual(self.pending(recs), [])

    def test_both_passes_counts_as_an_audit(self):
        """both-passes runs style-audit and first-reader together."""
        recs = [jake("go", T0), write(self.memo, T1), skill("both-passes", T2)]
        self.assertEqual(self.pending(recs), [])

    def test_the_plugin_name_of_the_skill_counts_as_an_audit(self):
        recs = [jake("go", T0), write(self.memo, T1),
                skill("ai-workflow-app:style-audit", T2)]
        self.assertEqual(self.pending(recs), [])

    def test_fixes_applied_after_the_audit_do_not_reopen_it(self):
        """The audit's own fixes are edits made after the audit. Counting
        them as new saves would send the assistant round again forever."""
        recs = [jake("go", T0), write(self.memo, T1), skill("style-audit", T2),
                edit(self.memo, T3)]
        self.assertEqual(self.pending(recs), [])

    def test_an_audit_that_names_the_file_covers_saves_after_it(self):
        """Replayed on the session of 2026-10-15: the assistant ran the audit
        on a memo saved in an earlier turn, then wrote the fixed memo out
        whole. That write is the audit's fix, and the audit named the file."""
        recs = [jake("go", T0), skill("style-audit", T1, args=self.memo),
                write(self.memo, T2)]
        self.assertEqual(self.pending(recs), [])

    def test_a_document_first_saved_after_the_audit_is_pending(self):
        other = os.path.join(self.proj, "notes.tex")
        recs = [jake("go", T0), write(self.memo, T1), skill("style-audit", T2),
                write(other, T3)]
        self.assertEqual(self.pending(recs), [other])

    def test_saves_before_jakes_last_message_do_not_count(self):
        """Work from an earlier turn was either audited then or shown to
        Jake already. The guard is about what this turn produced."""
        recs = [jake("first", T0), write(self.memo, T1),
                jake("second question", T2)]
        self.assertEqual(self.pending(recs), [])

    def test_injected_text_and_tool_results_are_not_jakes_message(self):
        """A system reminder or a tool result arriving after a save must not
        be read as a new message from Jake, which would hide the save."""
        recs = [jake("go", T0), write(self.memo, T1), tool_result(T2),
                injected("<system-reminder>note</system-reminder>", T3)]
        self.assertEqual(self.pending(recs), [self.memo])

    def test_jake_running_the_audit_himself_counts(self):
        recs = [jake("go", T0), write(self.memo, T1),
                injected("<command-name>/style-audit</command-name>", T2)]
        self.assertEqual(self.pending(recs), [])

    def test_reply_drafts_in_the_scratch_area_are_not_documents(self):
        """Replies are drafted in the scratchpad and checked with
        `style_gate.py check`; they are not documents Jake reads as files."""
        draft = os.path.join(self.scratch, "reply.md")
        recs = [jake("go", T0), write(draft, T1)]
        self.assertEqual(self.pending(recs), [])

    def test_files_under_dot_claude_are_not_documents(self):
        mem = os.path.join(self.home, ".claude", "projects", "p", "memory",
                           "note.md")
        recs = [jake("go", T0), write(mem, T1)]
        self.assertEqual(self.pending(recs), [])

    def test_code_files_are_not_documents(self):
        recs = [jake("go", T0),
                write(os.path.join(self.proj, "analysis.R"), T1),
                write(os.path.join(self.proj, "guard.py"), T1)]
        self.assertEqual(self.pending(recs), [])

    def test_each_document_is_listed_once(self):
        recs = [jake("go", T0), write(self.memo, T1), edit(self.memo, T2)]
        self.assertEqual(self.pending(recs), [self.memo])

    def test_one_file_reached_through_a_link_is_listed_once(self):
        """skills/ in this repository is a link to plugins/ai-workflow/skills,
        so one SKILL.md has two names."""
        link = os.path.join(self.root, "projlink")
        os.symlink(self.proj, link)
        open(self.memo, "w").close()
        recs = [jake("go", T0), write(self.memo, T1),
                edit(os.path.join(link, "memo.md"), T2)]
        self.assertEqual(self.pending(recs), [self.memo])


class TestBashSaves(GuardCase):
    """Documents are often changed by a script run through Bash rather than
    by Write or Edit. A command names files it reads as well as files it
    writes, so a named file counts only when it was modified while that
    command ran: after the command was issued and before its result came
    back. A file another command changed earlier, and this one only read,
    does not count. Replayed on the session of 2026-10-15, a looser rule
    (modified any time after Jake's message) listed codex/AGENTS.md, which
    `make agents-md` had rebuilt and a later `wc -c` had only read."""

    def stamp(self, path, iso):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("x\n")
        t = calendar.timegm(time.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S"))
        os.utime(path, (t, t))

    def test_a_file_a_command_changed_is_a_document(self):
        self.stamp(self.memo, "2026-10-15T20:01:02.000Z")
        recs = [jake("go", T0),
                tool("Bash", {"command": "python3 fix.py memo.md"}, T1,
                     cwd=self.proj),
                tool_result("2026-10-15T20:01:05.000Z")]
        self.assertEqual(self.pending(recs), [self.memo])

    def test_a_file_changed_earlier_and_only_read_now_is_not(self):
        self.stamp(self.memo, "2026-10-15T20:01:02.000Z")
        recs = [jake("go", T0),
                tool("Bash", {"command": "make build"}, T1, cwd=self.proj),
                tool_result("2026-10-15T20:01:05.000Z"),
                tool("Bash", {"command": "wc -c memo.md"}, T3,
                     cwd=self.proj, use_id="y"),
                tool_result("2026-10-15T20:03:01.000Z", use_id="y")]
        self.assertEqual(self.pending(recs), [])

    def test_a_file_a_command_only_read_is_not(self):
        self.stamp(self.memo, "2026-10-14T09:00:00.000Z")
        recs = [jake("go", T0),
                tool("Bash", {"command": "cat memo.md"}, T1, cwd=self.proj),
                tool_result(T2)]
        self.assertEqual(self.pending(recs), [])


class TestTheHook(GuardCase):

    def test_blocks_with_a_reason_naming_the_file_and_the_skill(self):
        code, out = self.run_hook([jake("go", T0), write(self.memo, T1)])
        self.assertEqual(code, 0)
        self.assertEqual(out["decision"], "block")
        self.assertIn(self.memo, out["reason"])
        self.assertIn("style-audit", out["reason"])

    def test_the_reason_is_plain_ascii(self):
        _, out = self.run_hook([jake("go", T0), write(self.memo, T1)])
        self.assertTrue(all(ord(c) <= 126 for c in out["reason"]))

    def test_says_nothing_when_every_document_was_audited(self):
        code, out = self.run_hook([jake("go", T0), write(self.memo, T1),
                                   skill("style-audit", T2)])
        self.assertEqual((code, out), (0, None))

    def test_never_blocks_twice_in_a_row(self):
        """Claude Code sets stop_hook_active when the assistant is already
        continuing because a Stop hook blocked. Blocking again could loop."""
        code, out = self.run_hook([jake("go", T0), write(self.memo, T1)],
                                  stop_hook_active=True)
        self.assertEqual((code, out), (0, None))

    def test_records_each_block_in_the_log(self):
        """So that how often the guard fires can be counted later."""
        self.run_hook([jake("go", T0), write(self.memo, T1)])
        with open(self.log, encoding="utf-8") as fh:
            rec = json.loads(fh.readline())
        self.assertEqual(rec["files"], [self.memo])

    def test_silent_inside_the_reply_checks_own_reader(self):
        """The second model that style_gate.py runs is itself a Claude
        session with Jake's hooks; it must never be blocked."""
        os.environ[ag.READER_MARK] = "1"
        try:
            code, out = self.run_hook([jake("go", T0), write(self.memo, T1)])
        finally:
            del os.environ[ag.READER_MARK]
        self.assertEqual((code, out), (0, None))


class TestFailsOpen(GuardCase):

    def run_raw(self, text):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = ag.run(text, self.log, home=self.home,
                          scratch_roots=(self.scratch,))
        return code, buf.getvalue()

    def test_unreadable_input_lets_the_turn_end(self):
        self.assertEqual(self.run_raw("not json"), (0, ""))

    def test_a_missing_transcript_lets_the_turn_end(self):
        self.assertEqual(self.run_raw(json.dumps(
            {"transcript_path": os.path.join(self.root, "none.jsonl")})),
            (0, ""))

    def test_corrupt_lines_are_skipped(self):
        path = os.path.join(self.root, "t.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{broken\n")
            fh.write(json.dumps(jake("go", T0)) + "\n")
            fh.write(json.dumps(write(self.memo, T1)) + "\n")
        self.assertEqual(ag.unaudited_documents(
            path, home=self.home, scratch_roots=(self.scratch,)), [self.memo])


if __name__ == "__main__":
    unittest.main()
