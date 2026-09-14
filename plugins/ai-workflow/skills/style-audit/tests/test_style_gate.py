#!/usr/bin/env python3
"""Unit tests for style_gate.py, the prose gate on Claude's replies to Jake.

The gate does NOT judge writing. style_scan.py flags candidates and SKILL.md
section 1 pass 2 decides. The gate's job is narrower: keep the violations
that need no judgment out of the replies Jake reads, and measure how often
they get through.

Four design facts the tests must protect:

  * PREVENTION, NOT CORRECTION. A Stop hook fires after Claude's text has
    already reached the terminal, and no hook event can retract displayed
    text. So a blocking gate would show Jake the flawed message and then a
    rewrite. He asked for one message. That rules out blocking, and moves
    the work to a UserPromptSubmit injection that lands immediately before
    generation instead of 28KB away at the top of context.

  * THE GATE NEVER BLOCKS. Every path returns 0. This is the headline
    safety property and it is asserted on the dirty path too, because the
    failure it prevents --- a Stop hook that exits 2 forever on a message
    it keeps re-reading --- costs Jake the session.

  * TWO TIERS, MEASURED. Over 329 assistant prose messages from 12 recent
    transcripts, 40% carried a mechanical violation (212 unicode em dashes,
    95 bold run-in openers, 14 em-dash + semicolon collisions) and 16%
    touched a judgment category. Only the mechanical tier admits no
    judgment, so only it is named as a fault in the injected reminder.
    "costs" is usually literal, and banning the word would train avoidance
    of an item instead of the habit. The reminder also carries the eight
    reading questions from SKILL.md section 0, added 2026-09-14 after the
    log showed the mechanical reminder working; those ask about the draft
    and name no words.

  * IT FAILS OPEN AND SILENT. Malformed JSON, a missing field, a raised
    exception: exit 0, no log line, no output. Losing one measurement is a
    smaller loss than a broken session.

Fenced code is skipped, reusing style_scan's fence handling: Claude shows
shell and R constantly, and 'sandbox', 'pipeline' and 'costs' are ordinary
words there. Inline code is skipped too, so that a reply reporting which
word the gate matched does not count as a violation of its own.

Note on ASCII: this file tests unicode detection without containing unicode.
Offending characters are written as Python escapes, so the file satisfies the
rule it enforces.

Run: python3 test_style_gate.py    (or via the repo-root Makefile: make test)
"""

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
import style_gate as sg  # noqa: E402

EM_DASH = "\u2014"
EN_DASH = "\u2013"


def stop_event(message, prompt_id="p1"):
    """A Stop event as the harness delivers it on stdin."""
    return json.dumps({"hook_event_name": "Stop",
                       "prompt_id": prompt_id,
                       "session_id": "s1",
                       "last_assistant_message": message})


class GateCase(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.log = os.path.join(self._tmp.name, "sub", "style_gate.jsonl")

    def tearDown(self):
        self._tmp.cleanup()

    def run_stop(self, message, prompt_id="p1"):
        """Run the stop entry point; return (exit_code, parsed_stdout_or_None)."""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["stop"], stop_event(message, prompt_id), self.log)
        out = buf.getvalue().strip()
        return code, (json.loads(out) if out else None)

    def records(self):
        """Every JSON record written to the log so far."""
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as fh:
            return [json.loads(ln) for ln in fh if ln.strip()]

    def context_of(self, payload):
        return payload["hookSpecificOutput"]["additionalContext"]


class TestNeverBlocks(GateCase):
    """The property whose failure costs Jake the session."""

    def test_clean_message_returns_zero(self):
        code, _ = self.run_stop("The estimand is the average treatment effect.")
        self.assertEqual(code, 0)

    def test_mechanical_violation_returns_zero(self):
        code, _ = self.run_stop("The estimand %s not the estimate." % EM_DASH)
        self.assertEqual(code, 0)

    def test_judgment_candidate_returns_zero(self):
        code, _ = self.run_stop("Running it on the cluster costs three days.")
        self.assertEqual(code, 0)

    def test_repeated_identical_dirty_messages_return_zero(self):
        """Nothing forces a re-read, so nothing can loop."""
        dirty = "a %s b" % EM_DASH
        for _ in range(3):
            code, _ = self.run_stop(dirty)
            self.assertEqual(code, 0)


class TestLogging(GateCase):
    """The log is the whole point: it turns 40% into a number we can watch."""

    def test_mechanical_violation_is_logged_with_tier_and_category(self):
        self.run_stop("The estimand %s not the estimate." % EM_DASH)
        recs = self.records()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["tier"], "mechanical")
        self.assertIn("unicode", recs[0]["categories"])

    def test_en_dash_is_logged(self):
        self.run_stop("See pages 97%s124." % EN_DASH)
        self.assertIn("unicode", self.records()[0]["categories"])

    def test_bold_run_in_opener_is_logged(self):
        self.run_stop("**What it gives up.** Three things.")
        self.assertIn("bold-run-in-opener", self.records()[0]["categories"])

    def test_dash_semicolon_is_logged(self):
        self.run_stop("The test is exact --- it permutes; the bound is not.")
        self.assertIn("dash-semicolon", self.records()[0]["categories"])

    def test_judgment_only_violation_logs_the_judgment_tier(self):
        self.run_stop("Clustering at the school level is appropriate.")
        self.assertEqual(self.records()[0]["tier"], "judgment")

    def test_both_tiers_logs_as_mechanical(self):
        """Mechanical is the tier that admits no argument, so it wins the
        label when a message carries both."""
        self.run_stop("It costs three days %s more than we have." % EM_DASH)
        self.assertEqual(self.records()[0]["tier"], "mechanical")

    def test_clean_message_writes_no_record(self):
        self.run_stop("The estimand is the average treatment effect.")
        self.assertEqual(self.records(), [])

    def test_records_append_rather_than_overwrite(self):
        self.run_stop("a %s b" % EM_DASH, prompt_id="p1")
        self.run_stop("c %s d" % EM_DASH, prompt_id="p2")
        self.assertEqual(len(self.records()), 2)

    def test_record_carries_a_count_and_a_session_id(self):
        self.run_stop("a %s b %s c" % (EM_DASH, EM_DASH))
        rec = self.records()[0]
        self.assertEqual(rec["count"], 2)
        self.assertEqual(rec["session_id"], "s1")

    def test_missing_log_directory_is_created(self):
        """The log path has a directory component that does not exist."""
        self.assertFalse(os.path.exists(os.path.dirname(self.log)))
        self.run_stop("a %s b" % EM_DASH)
        self.assertTrue(os.path.exists(self.log))


class TestInjectedNote(GateCase):
    """A non-blocking hook's context lands at the start of the next turn."""

    def test_note_names_the_matched_text(self):
        _, out = self.run_stop("**What it gives up.** Three things.")
        self.assertIn("What it gives up", self.context_of(out))

    def test_note_tells_claude_not_to_surface_it(self):
        """Otherwise the note becomes the doubled message by another route."""
        _, out = self.run_stop("a %s b" % EM_DASH)
        self.assertIn("do not mention", self.context_of(out).lower())

    def test_note_is_pure_ascii(self):
        _, out = self.run_stop("a %s b" % EM_DASH)
        self.assertTrue(all(ord(c) <= 126 for c in self.context_of(out)),
                        "the gate must not inject the character it bans")

    def test_clean_message_produces_no_output_at_all(self):
        code, out = self.run_stop("The estimand is the average treatment effect.")
        self.assertEqual(code, 0)
        self.assertIsNone(out, "56% of messages are clean; that path stays silent")

    def test_payload_is_a_stop_envelope(self):
        _, out = self.run_stop("a %s b" % EM_DASH)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "Stop")


class TestFencedCodeIsSkipped(GateCase):

    def test_offenders_only_inside_a_fence_are_ignored(self):
        msg = ("Here is the command:\n\n```bash\n"
               "# costs and pipeline and sandbox\nrun --sandbox\n```\n")
        code, out = self.run_stop(msg)
        self.assertEqual(code, 0)
        self.assertIsNone(out)
        self.assertEqual(self.records(), [])

    def test_prose_offender_beside_a_fence_is_caught(self):
        msg = "The estimand %s below.\n\n```r\nx <- 1  # costs\n```\n" % EM_DASH
        self.run_stop(msg)
        self.assertIn("unicode", self.records()[0]["categories"])

    def test_unclosed_fence_terminates_without_raising(self):
        code, _ = self.run_stop("```bash\nrun\n")
        self.assertEqual(code, 0)


class TestInlineCodeIsSkipped(GateCase):
    """A reply that reports a finding must not itself become one.

    On 2026-09-01 the gate caught an idiom in a reply, and the next reply,
    which told Jake which word had been caught, quoted the word and was
    logged in turn: two log lines from one violation. Counting dirty turns
    over time would run high by however many such reports there are, and it
    would run high exactly in the sessions spent working on the gate.
    Naming an offender between code marks is how a report says which word
    without using it.
    """

    def test_offender_between_code_marks_is_not_a_finding(self):
        self.assertEqual(sg.scan_message("the pattern for `lands` fired"), [])

    def test_a_report_of_a_finding_adds_no_log_line(self):
        code, out = self.run_stop(
            "The scanner caught `lands` and `costs` in the last reply.")
        self.assertEqual(code, 0)
        self.assertIsNone(out)
        self.assertEqual(self.records(), [])

    def test_the_same_words_in_prose_still_log(self):
        self.run_stop("The argument lands and the delay costs us a week.")
        recs = self.records()
        self.assertEqual(len(recs), 1)
        self.assertIn("idiom", recs[0]["categories"])


class TestPreflight(unittest.TestCase):
    """The UserPromptSubmit injection: the only part that can prevent rather
    than record, because it arrives before Claude generates."""

    def run_preflight(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["preflight"], json.dumps(
                {"hook_event_name": "UserPromptSubmit", "prompt": "hi"}), None)
        return code, json.loads(buf.getvalue())

    def test_returns_zero(self):
        code, _ = self.run_preflight()
        self.assertEqual(code, 0)

    def test_envelope_names_the_right_event(self):
        _, out = self.run_preflight()
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"],
                         "UserPromptSubmit")

    def test_names_all_three_mechanical_rules(self):
        """Only the rules that admit no judgment. A longer list would teach
        avoidance of items instead of the habit."""
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"].lower()
        self.assertIn("unicode", ctx)
        self.assertIn("bold", ctx)
        self.assertIn("semicolon", ctx)

    def test_does_not_name_judgment_categories(self):
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"].lower()
        for word in ("costs", "appropriate", "load-bearing"):
            self.assertNotIn(word, ctx)

    def test_injection_is_pure_ascii(self):
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertTrue(all(ord(c) <= 126 for c in ctx))

    def test_injection_is_short(self):
        """It rides on every single turn, so length is not free.

        The cap was 600 characters while the injection named only the three
        mechanical faults. It rose on 2026-09-14, when the injection took on
        the reading check as well, and the reason is in the gate's own log:
        from 2026-09-01 to 2026-09-14 the log holds 15 replies with a
        mechanical fault against a pre-gate rate of 40 percent of all
        replies, so the adjacent reminder works for what it names, and what
        Jake still stops on is what it did not name. Eight questions and the
        instruction to scan the draft fit in about 1500 characters, which is
        roughly 350 tokens on every turn.
        """
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertLess(len(ctx), 1700)

    def test_tells_claude_to_write_the_draft_to_a_file_and_scan_it(self):
        """CLAUDE.md already says to write the draft to a file and run the
        scanner over it. The injection repeats that instruction because the
        one 28KB away kept getting skipped and the adjacent one did not."""
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("style_scan.py", ctx)
        self.assertIn("file", ctx.lower())

    def test_names_every_reading_question(self):
        """The eight questions of SKILL.md section 0 are the check on a reply,
        since the scanner locates 1 of the 47 stops Jake quoted back. Each is
        identified by a phrase from its heading, in the order the skill gives
        them, so a question dropped or reworded out of recognition fails
        here."""
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"].lower()
        phrases = ("technical term", "what question it answers", "resolve",
                   "person", "pronoun", "adds nothing", "therefore",
                   "did not give")
        positions = [ctx.find(ph) for ph in phrases]
        for ph, pos in zip(phrases, positions):
            self.assertNotEqual(pos, -1, "injection does not name: " + ph)
        self.assertEqual(positions, sorted(positions),
                         "questions are out of the order section 0 gives")

    def test_question_count_matches_skill_section_0(self):
        """The gate carries its own copy of the questions, as it carries the
        scanner's patterns through style_scan, and a copy drifts. This pins
        the number of questions in the injection to the number of bold
        numbered questions in section 0 of SKILL.md, so adding a question to
        one file and not the other fails loudly."""
        skill = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "SKILL.md")
        with open(skill, encoding="utf-8") as fh:
            text = fh.read()
        section = text.split("## 0.", 1)[1].split("## 1.", 1)[0]
        in_skill = sum(1 for ln in section.splitlines()
                       if ln[:1].isdigit() and ". **" in ln[:6])
        self.assertEqual(in_skill, 8)
        self.assertEqual(len(sg.QUESTIONS), in_skill)

    def test_questions_name_no_particular_words(self):
        """The questions ask about the draft, never about a word. A question
        naming a word would be a ban list by another route."""
        for q in sg.QUESTIONS:
            self.assertNotIn('"', q, "a quoted word in a question: " + q)


class TestFailsOpen(GateCase):
    """A broken gate must never wedge or pollute the session."""

    def test_malformed_json_exits_zero_and_silent(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["stop"], "{not json at all", self.log)
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")
        self.assertEqual(self.records(), [])

    def test_missing_message_field_exits_zero(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["stop"], json.dumps({"hook_event_name": "Stop"}),
                           self.log)
        self.assertEqual(code, 0)

    def test_empty_and_whitespace_messages_exit_zero(self):
        for msg in ("", "   \n\n  "):
            code, out = self.run_stop(msg)
            self.assertEqual(code, 0)
            self.assertIsNone(out)

    def test_scan_failure_exits_zero(self):
        original = sg.scan_message
        sg.scan_message = lambda _t: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            code, out = self.run_stop("a %s b" % EM_DASH)
        finally:
            sg.scan_message = original
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    def test_unwritable_log_still_exits_zero(self):
        """Measurement is optional; the session is not."""
        blocker = os.path.join(self._tmp.name, "blocker")
        open(blocker, "w").close()   # a plain file where a directory is needed
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["stop"], stop_event("a %s b" % EM_DASH),
                           os.path.join(blocker, "style.jsonl"))
        self.assertEqual(code, 0)

    def test_unknown_subcommand_exits_zero_and_silent(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["wat"], "{}", self.log)
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")


def posttool_event(tool_name, tool_input):
    """A PostToolUse event as the harness delivers it on stdin."""
    return json.dumps({"hook_event_name": "PostToolUse",
                       "session_id": "s1",
                       "tool_name": tool_name,
                       "tool_input": tool_input,
                       "tool_response": {}})


class TestPostTool(GateCase):
    """The gate on files: after a tool writes prose, scan the file.

    Jake asked on 2026-09-14 that documents get the audit without his
    having to invoke the skill by name. The reply gate cannot see a file,
    so this third entry point runs on PostToolUse. It scans the file a Write
    or Edit named, and, because in some sessions the assistant writes files
    through shell heredocs and sed rather than the Write tool, it also reads
    a Bash command for prose paths and scans any it names that changed in
    the last minute. It injects the findings as context, so the next thing
    the assistant does is fix the file rather than report it done. Like the
    other two entry points it never blocks and fails open.
    """

    PROSE_EXTENSIONS = (".md", ".tex", ".Rmd", ".qmd")

    def prose_file(self, name, text):
        path = os.path.join(self._tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def run_posttool(self, tool_name, tool_input):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], posttool_event(tool_name, tool_input),
                           self.log)
        out = buf.getvalue().strip()
        return code, (json.loads(out) if out else None)

    def test_write_of_a_dirty_md_file_injects_a_note_naming_the_file(self):
        path = self.prose_file("memo.md", "The estimand %s not the estimate.\n" % EM_DASH)
        code, out = self.run_posttool("Write", {"file_path": path, "content": "x"})
        self.assertEqual(code, 0)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PostToolUse")
        ctx = self.context_of(out)
        self.assertIn("memo.md", ctx)
        self.assertIn("unicode", ctx)

    def test_each_prose_extension_is_scanned(self):
        for ext in self.PROSE_EXTENSIONS:
            path = self.prose_file("draft" + ext, "a %s b\n" % EM_DASH)
            _, out = self.run_posttool("Edit", {"file_path": path})
            self.assertIsNotNone(out, "not scanned: " + ext)

    def test_extension_case_does_not_matter(self):
        path = self.prose_file("draft.RMD", "a %s b\n" % EM_DASH)
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertIsNotNone(out)

    def test_a_code_file_is_ignored(self):
        path = self.prose_file("gate.py", "# a %s b\n" % EM_DASH)
        code, out = self.run_posttool("Write", {"file_path": path})
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    def test_a_clean_file_is_silent(self):
        path = self.prose_file("memo.md", "The estimand is the average treatment effect.\n")
        code, out = self.run_posttool("Write", {"file_path": path})
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    def test_fenced_code_in_markdown_is_skipped(self):
        path = self.prose_file("memo.md", "Run this:\n\n```r\nx <- 1  # costs\n```\n")
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertIsNone(out)

    def test_a_judgment_candidate_is_reported_too(self):
        """A file is not a reply: the note can afford to name candidates,
        since the assistant is about to reread the file anyway."""
        path = self.prose_file("memo.md", "Clustering at the school level is appropriate.\n")
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertIn("vague-evaluative", self.context_of(out))

    def test_attention_categories_stay_out_of_the_note(self):
        path = self.prose_file("memo.md", "We ran it, and the rest follows.\n")
        _, out = self.run_posttool("Write", {"file_path": path})
        if out is not None:
            self.assertNotIn("trailing-clause", self.context_of(out))

    def test_note_names_the_line_number(self):
        path = self.prose_file("memo.md", "clean\nclean\na %s b\n" % EM_DASH)
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertIn("3", self.context_of(out))

    def test_note_says_to_fix_the_file_and_read_the_questions(self):
        """The scan is the mechanical half. The note says so, and points at
        the eight questions, so a clean scan is not mistaken for a clean
        file."""
        path = self.prose_file("memo.md", "a %s b\n" % EM_DASH)
        _, out = self.run_posttool("Write", {"file_path": path})
        ctx = self.context_of(out).lower()
        self.assertIn("fix", ctx)
        self.assertIn("eight questions", ctx)

    def test_note_is_pure_ascii(self):
        path = self.prose_file("memo.md", "a %s b\n" % EM_DASH)
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertTrue(all(ord(c) <= 126 for c in self.context_of(out)))

    def test_bash_command_naming_a_fresh_prose_file_is_scanned(self):
        path = self.prose_file("notes.qmd", "a %s b\n" % EM_DASH)
        cmd = "cat > %s <<'EOF'\nwhatever\nEOF" % path
        _, out = self.run_posttool("Bash", {"command": cmd})
        self.assertIsNotNone(out)
        self.assertIn("notes.qmd", self.context_of(out))

    def test_bash_command_naming_a_stale_prose_file_is_ignored(self):
        """A command that only reads an old file must not trigger a scan of
        it, so only files changed within the last minute count."""
        path = self.prose_file("old.md", "a %s b\n" % EM_DASH)
        old = time.time() - 600
        os.utime(path, (old, old))
        _, out = self.run_posttool("Bash", {"command": "cat %s" % path})
        self.assertIsNone(out)

    def test_bash_command_naming_a_missing_file_is_ignored(self):
        cmd = "cat %s" % os.path.join(self._tmp.name, "nowhere.tex")
        code, out = self.run_posttool("Bash", {"command": cmd})
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    def test_bash_command_with_no_prose_path_is_silent(self):
        code, out = self.run_posttool("Bash", {"command": "ls -la && git status"})
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    def test_dirty_file_is_logged_with_its_path(self):
        path = self.prose_file("memo.md", "a %s b\n" % EM_DASH)
        self.run_posttool("Write", {"file_path": path})
        recs = self.records()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["file"], path)
        self.assertEqual(recs[0]["tier"], "mechanical")

    def test_missing_tool_input_exits_zero_and_silent(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], json.dumps({"hook_event_name": "PostToolUse",
                                                     "tool_name": "Write"}), self.log)
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_malformed_json_exits_zero_and_silent(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], "{nope", self.log)
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_unreadable_file_exits_zero_and_silent(self):
        path = os.path.join(self._tmp.name, "gone.md")
        code, out = self.run_posttool("Write", {"file_path": path})
        self.assertEqual(code, 0)
        self.assertIsNone(out)


class TestTierMembershipIsOneLine(unittest.TestCase):
    """If the judgment tier should ever be treated as mechanical, that is a
    one-line edit to a constant, not a change spread through the code."""

    def test_mechanical_categories_declared_in_one_place(self):
        self.assertEqual(set(sg.MECHANICAL),
                         {"unicode", "bold-run-in-opener", "dash-semicolon"})


class AttentionCategoryTests(unittest.TestCase):
    """Some categories direct a second look rather than report a fault.

    `trailing-clause` flags about one line in fourteen. That is cheap when a
    reader is going through a draft anyway and asking, at each flag, whether
    the sentence splits in two and whether the second half says anything. It
    is not cheap in the note this gate injects, which Jake reads in his
    terminal after every reply: a category firing that often would fill his
    screen with candidates and bury the ones that admit no argument.

    So the gate logs it and leaves it out of the note.
    """

    def test_trailing_clause_is_not_named_in_the_note(self):
        findings = [("f", 1, "trailing-clause", ", which is what"),
                    ("f", 2, "unicode", "\u2014")]
        note = sg.build_note(findings)
        self.assertNotIn("trailing-clause", note)
        self.assertIn("unicode", note)

    def test_a_reply_with_only_attention_categories_gets_no_note_at_all(self):
        self.assertIsNone(sg.build_note([("f", 1, "trailing-clause", ", and the")]))

    def test_the_category_is_still_logged(self):
        """Dropping it from the note must not drop it from the measurement."""
        self.assertIn("trailing-clause", sg.ATTENTION)


if __name__ == "__main__":
    unittest.main(verbosity=2)
