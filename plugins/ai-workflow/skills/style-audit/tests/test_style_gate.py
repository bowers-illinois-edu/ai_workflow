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

    def test_clean_message_writes_one_record_with_no_categories(self):
        """Until 2026-09-20 a clean reply wrote nothing, so the log counted
        dirty replies only. It now records every reply, because the field
        Jake asked for, whether the reply went through `check`, has to be
        counted over all replies and not over the dirty ones."""
        self.run_stop("The estimand is the average treatment effect.")
        recs = self.records()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["categories"], [])

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
        self.assertEqual(self.records()[0]["categories"], [])

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
        # Every reply is logged since 2026-09-20; the point here is that the
        # words between code marks are not counted as findings.
        self.assertEqual(self.records()[0]["categories"], [])
        self.assertEqual(self.records()[0]["tier"], "clean")

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
        mechanical faults, and 1700 from 2026-09-14 to 2026-09-20 while it
        also carried the eight reading questions. On 2026-09-20 the questions
        left it: between 2026-09-14 and 2026-09-20 Jake objected to 55 chat
        replies, every one written with the questions in front of the
        writer, and he traced three faults in one reply to the rules
        themselves, which the writer had satisfied by fragment, label and
        substitute word. The questions now go to the second reader, which
        `check` runs, and the injection says to run it.
        """
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertLess(len(ctx), 900)

    def test_tells_claude_to_write_the_draft_to_a_file_and_check_it(self):
        """The one instruction that has to survive: write the draft to a
        file and run the check on it, with the command spelled out so that
        nothing has to be looked up."""
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("style_gate.py check", ctx)
        self.assertIn(os.path.abspath(sg.__file__), ctx)
        self.assertIn("file", ctx.lower())

    def test_says_to_open_with_the_answer_and_what_is_needed(self):
        """The two reply faults the reader cannot fix after the fact: not
        answering the question asked, 4 of Jake's 55 objections, and burying
        what he is being asked for, 12 of them."""
        _, out = self.run_preflight()
        ctx = " ".join(out["hookSpecificOutput"]["additionalContext"].lower().split())
        self.assertIn("answer", ctx)
        self.assertIn("need from him", ctx)

    def test_says_to_open_with_what_the_question_is_for(self):
        """Jake, 2026-10-15: a reply can begin with a sentence or two on how
        the assistant understands the point of the task and how the reply
        serves it, and when that is hard to say it is time to stop and ask.
        The opening restates his question with its purpose, not just the
        question."""
        _, out = self.run_preflight()
        ctx = " ".join(out["hookSpecificOutput"]["additionalContext"].lower().split())
        self.assertIn("wants it for", ctx)

    def test_names_no_reading_question(self):
        """The questions belong to the reader now. A question in front of
        the writer is a rule, and the writer satisfies rules by fragment."""
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"].lower()
        for ph in ("pronoun", "antecedent", "therefore", "adds nothing"):
            self.assertNotIn(ph, ctx)

    def test_question_count_matches_skill_section_0(self):
        """The gate keeps a copy of the questions for the reader's prompt
        and for the skill; a copy drifts. This pins the number of questions
        to the number of bold numbered questions in section 0 of SKILL.md,
        so adding a question to one file and not the other fails loudly."""
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

    PROSE_EXTENSIONS = (".md", ".tex", ".Rmd", ".qmd", ".txt")

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

    def run_posttool_in(self, cwd, tool_name, tool_input):
        """As run_posttool, with the working directory the harness reports."""
        event = json.loads(posttool_event(tool_name, tool_input))
        event["cwd"] = cwd
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], json.dumps(event), self.log)
        out = buf.getvalue().strip()
        return code, (json.loads(out) if out else None)

    def test_bash_route_finds_a_fresh_prose_file_the_command_hides(self):
        """Jake raised this on 2026-09-14: `f=memo.md; cat > $f` names no
        file in its text. So after a Bash command the gate also looks under
        the working directory for any prose file changed in the last minute,
        whatever the command said."""
        path = self.prose_file("memo.md", "a %s b\n" % EM_DASH)
        _, out = self.run_posttool_in(self._tmp.name, "Bash",
                                      {"command": "f=memo.md; cat > $f"})
        self.assertIsNotNone(out)
        self.assertIn("memo.md", self.context_of(out))

    def test_bash_route_walk_ignores_old_files(self):
        path = self.prose_file("old.md", "a %s b\n" % EM_DASH)
        old = time.time() - 600
        os.utime(path, (old, old))
        _, out = self.run_posttool_in(self._tmp.name, "Bash",
                                      {"command": "ls"})
        self.assertIsNone(out)

    def test_bash_route_walk_skips_git_and_hidden_directories(self):
        for sub in (".git", ".cache"):
            os.makedirs(os.path.join(self._tmp.name, sub))
            self.prose_file(os.path.join(sub, "x.md"), "a %s b\n" % EM_DASH)
        _, out = self.run_posttool_in(self._tmp.name, "Bash",
                                      {"command": "ls"})
        self.assertIsNone(out)

    def test_bash_route_reports_a_file_once_when_both_routes_find_it(self):
        path = self.prose_file("memo.md", "a %s b\n" % EM_DASH)
        _, out = self.run_posttool_in(self._tmp.name, "Bash",
                                      {"command": "cat > %s" % path})
        self.assertEqual(self.context_of(out).count("memo.md"), 1)

    def test_bash_route_without_a_cwd_still_reads_the_command(self):
        path = self.prose_file("memo.md", "a %s b\n" % EM_DASH)
        _, out = self.run_posttool("Bash", {"command": "cat > %s" % path})
        self.assertIsNotNone(out)

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


def make_docx(path, paragraphs):
    """A minimal Word file: a zip holding word/document.xml with one w:p per
    paragraph. Word writes far more than this, but the text of a document is
    entirely inside w:t elements, which is all the extractor reads."""
    import zipfile
    body = "".join(
        "<w:p><w:r><w:t>%s</w:t></w:r></w:p>" % p for p in paragraphs)
    xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<w:document xmlns:w="http://schemas.openxmlformats.org/'
           'wordprocessingml/2006/main"><w:body>%s</w:body></w:document>'
           % body)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("word/document.xml", xml)
    return path


class TestDocx(GateCase):
    """Word files, which Jake meets through collaborators on Google Drive.

    A .docx is a zip archive, and its text sits in w:t elements inside
    w:p paragraphs in word/document.xml. Scanning the raw bytes would report
    the markup, so the gate extracts one line of text per paragraph and
    scans those, and the note numbers paragraphs rather than lines.
    """

    def run_posttool(self, tool_name, tool_input):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], posttool_event(tool_name, tool_input),
                           self.log)
        out = buf.getvalue().strip()
        return code, (json.loads(out) if out else None)

    def test_paragraph_text_is_scanned_and_markup_is_not(self):
        path = make_docx(os.path.join(self._tmp.name, "memo.docx"),
                         ["The estimand is the average treatment effect.",
                          "The estimate %s not the estimand." % EM_DASH])
        code, out = self.run_posttool("Write", {"file_path": path})
        self.assertEqual(code, 0)
        ctx = self.context_of(out)
        self.assertIn("memo.docx", ctx)
        self.assertIn("unicode", ctx)
        self.assertNotIn("w:", ctx, "markup reached the note")

    def test_note_numbers_the_paragraph(self):
        path = make_docx(os.path.join(self._tmp.name, "memo.docx"),
                         ["clean", "clean", "a %s b" % EM_DASH])
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertIn("paragraph 3", self.context_of(out))

    def test_a_clean_docx_is_silent(self):
        path = make_docx(os.path.join(self._tmp.name, "memo.docx"),
                         ["The estimand is the average treatment effect."])
        code, out = self.run_posttool("Write", {"file_path": path})
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    def test_a_docx_that_is_not_a_zip_is_silent(self):
        path = os.path.join(self._tmp.name, "broken.docx")
        with open(path, "w") as fh:
            fh.write("not a zip %s" % EM_DASH)
        code, out = self.run_posttool("Write", {"file_path": path})
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    def test_docx_is_found_by_the_bash_route(self):
        path = make_docx(os.path.join(self._tmp.name, "memo.docx"),
                         ["a %s b" % EM_DASH])
        event = json.loads(posttool_event("Bash", {"command": "pandoc memo.md -o memo.docx"}))
        event["cwd"] = self._tmp.name
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sg.main(["posttool"], json.dumps(event), self.log)
        self.assertIn("memo.docx", buf.getvalue())

    def test_extractor_joins_runs_within_a_paragraph(self):
        """Word splits one sentence across several w:r runs when formatting
        changes mid-sentence. The scan must see the sentence whole, or a
        pattern spanning two runs is missed."""
        import zipfile
        path = os.path.join(self._tmp.name, "runs.docx")
        xml = ('<w:document xmlns:w="http://schemas.openxmlformats.org/'
               'wordprocessingml/2006/main"><w:body><w:p>'
               '<w:r><w:t>Clustering here is </w:t></w:r>'
               '<w:r><w:t>appropriate.</w:t></w:r>'
               '</w:p></w:body></w:document>')
        with zipfile.ZipFile(path, "w") as zf:
            zf.writestr("word/document.xml", xml)
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertIn("vague-evaluative", self.context_of(out))


class TestChangeDirectory(GateCase):
    """A command that starts with `cd` names its files relative to the new
    directory, and the harness reports only the directory the session
    started in. Jake asked on 2026-09-14 that this case be covered. The gate
    reads each `cd` out of the command, follows them in order, and resolves
    relative names and the modification-time search against the result.
    """

    def run_bash(self, cwd, command):
        event = json.loads(posttool_event("Bash", {"command": command}))
        event["cwd"] = cwd
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], json.dumps(event), self.log)
        out = buf.getvalue().strip()
        return code, (json.loads(out) if out else None)

    def dirty(self, directory, name):
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("a %s b\n" % EM_DASH)
        return path

    def test_relative_name_after_an_absolute_cd(self):
        other = os.path.join(self._tmp.name, "elsewhere")
        self.dirty(other, "memo.md")
        _, out = self.run_bash(self._tmp.name, "cd %s && cat > memo.md" % other)
        self.assertIsNotNone(out)
        self.assertIn("memo.md", self.context_of(out))

    def test_relative_cd_is_taken_from_the_reported_cwd(self):
        self.dirty(os.path.join(self._tmp.name, "sub"), "memo.md")
        _, out = self.run_bash(self._tmp.name, "cd sub && cat > memo.md")
        self.assertIsNotNone(out)

    def test_hidden_name_after_cd_is_found_by_the_search(self):
        other = os.path.join(self._tmp.name, "elsewhere")
        self.dirty(other, "memo.md")
        _, out = self.run_bash(self._tmp.name,
                               "cd %s && f=memo.md; cat > $f" % other)
        self.assertIsNotNone(out)

    def test_quoted_directory_with_a_space(self):
        other = os.path.join(self._tmp.name, "dir with space")
        self.dirty(other, "memo.md")
        _, out = self.run_bash(self._tmp.name,
                               'cd "%s" && cat > memo.md' % other)
        self.assertIsNotNone(out)

    def test_two_cds_are_followed_in_order(self):
        deep = os.path.join(self._tmp.name, "a", "b")
        self.dirty(deep, "memo.md")
        _, out = self.run_bash(self._tmp.name, "cd a && cd b && cat > memo.md")
        self.assertIsNotNone(out)

    def test_cd_to_a_missing_directory_is_silent(self):
        code, out = self.run_bash(self._tmp.name,
                                  "cd /no/such/dir && cat > memo.md")
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    def test_cd_with_no_argument_means_home(self):
        """`cd` alone goes home. The gate follows it rather than staying put,
        so a file written there is looked for in the right place; the test
        only asks that nothing breaks, since it must not write to $HOME."""
        code, _ = self.run_bash(self._tmp.name, "cd && ls")
        self.assertEqual(code, 0)


class TestUncheckedFormats(GateCase):
    """Formats the scanner cannot read. Jake chose on 2026-09-14 to leave
    .rtf out and asked instead for a warning, worded to him, that the
    writing rules are not checked on such a file. The note goes to the
    assistant, so it tells the assistant to pass that warning on in the
    reply."""

    def run_posttool(self, tool_name, tool_input, cwd=None):
        event = json.loads(posttool_event(tool_name, tool_input))
        if cwd:
            event["cwd"] = cwd
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], json.dumps(event), self.log)
        out = buf.getvalue().strip()
        return code, (json.loads(out) if out else None)

    def rtf(self, name="notes.rtf"):
        path = os.path.join(self._tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{\\rtf1\\ansi The estimate %s not the estimand.}" % EM_DASH)
        return path

    def test_writing_an_rtf_file_warns_and_says_to_tell_jake(self):
        path = self.rtf()
        code, out = self.run_posttool("Write", {"file_path": path})
        self.assertEqual(code, 0)
        ctx = self.context_of(out)
        self.assertIn("notes.rtf", ctx)
        self.assertIn("not checked", ctx.lower())
        self.assertIn("tell jake", ctx.lower())

    def test_rtf_content_is_not_scanned(self):
        """The em dash inside the file must not appear as a finding: the
        warning is the whole note, since the scanner cannot read the
        format."""
        path = self.rtf()
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertNotIn("unicode", self.context_of(out))

    def test_rtf_named_in_a_bash_command_warns(self):
        path = self.rtf()
        _, out = self.run_posttool("Bash", {"command": "pandoc memo.md -o %s" % path})
        self.assertIn("notes.rtf", self.context_of(out))

    def test_fresh_rtf_found_by_the_search_warns(self):
        self.rtf()
        _, out = self.run_posttool("Bash", {"command": "f=notes.rtf; cat > $f"},
                                   cwd=self._tmp.name)
        self.assertIsNotNone(out)

    def test_rtf_warning_is_logged_as_unchecked(self):
        path = self.rtf()
        self.run_posttool("Write", {"file_path": path})
        recs = self.records()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["tier"], "unchecked")
        self.assertEqual(recs[0]["file"], path)

    def test_the_warning_is_pure_ascii(self):
        path = self.rtf()
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertTrue(all(ord(c) <= 126 for c in self.context_of(out)))


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



class TestFileNoteRepeats(GateCase):
    """The file gate reports only what is new since it last scanned a file
    in the same session.

    Measured 2026-09-20 over the gate's own log: from 2026-09-14 the file
    gate sent 2156 notes, and 1675 of them, 78 percent, were byte-identical
    to the note it had just sent for the same file. Each note puts up to 30
    matched phrases in front of the assistant while it drafts, which is the
    ban-list-in-context mechanism Jake identified on 2026-08-15 as making
    the prose worse. A file that was dirty before the edit and is equally
    dirty after it has told the assistant nothing new.

    Findings are compared by category and matched text, not line number,
    because an edit above a finding moves its line without changing it.
    """

    def prose_file(self, name, text):
        path = os.path.join(self._tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def run_posttool(self, tool_name, tool_input, session="s1"):
        event = json.loads(posttool_event(tool_name, tool_input))
        event["session_id"] = session
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], json.dumps(event), self.log)
        out = buf.getvalue().strip()
        return code, (json.loads(out) if out else None)

    def test_second_scan_with_the_same_findings_is_silent(self):
        path = self.prose_file("memo.md", "The estimand %s the estimate.\n" % EM_DASH)
        _, first = self.run_posttool("Write", {"file_path": path})
        self.assertIsNotNone(first)
        code, second = self.run_posttool("Edit", {"file_path": path})
        self.assertEqual(code, 0)
        self.assertIsNone(second)

    def test_only_the_new_finding_is_reported_on_a_rescan(self):
        path = self.prose_file("memo.md", "The estimand %s the estimate.\n" % EM_DASH)
        self.run_posttool("Write", {"file_path": path})
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("\nThe design is appropriate here.\n")
        _, out = self.run_posttool("Edit", {"file_path": path})
        ctx = self.context_of(out)
        self.assertIn("appropriate", ctx)
        self.assertNotIn("U+2014", ctx)

    def test_a_finding_that_moved_lines_is_not_new(self):
        path = self.prose_file("memo.md", "The estimand %s the estimate.\n" % EM_DASH)
        self.run_posttool("Write", {"file_path": path})
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("A new clean first line.\n\nThe estimand %s the estimate.\n" % EM_DASH)
        _, out = self.run_posttool("Edit", {"file_path": path})
        self.assertIsNone(out)

    def test_a_fixed_finding_produces_no_note(self):
        path = self.prose_file("memo.md", "The estimand %s the estimate.\n" % EM_DASH)
        self.run_posttool("Write", {"file_path": path})
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("The estimand --- the estimate.\n")
        _, out = self.run_posttool("Edit", {"file_path": path})
        self.assertIsNone(out)

    def test_another_session_gets_the_full_note(self):
        """A second session has not seen the first session's note."""
        path = self.prose_file("memo.md", "The estimand %s the estimate.\n" % EM_DASH)
        self.run_posttool("Write", {"file_path": path}, session="s1")
        _, out = self.run_posttool("Write", {"file_path": path}, session="s2")
        self.assertIn("U+2014", self.context_of(out))

    def test_a_repeat_is_not_logged_as_a_dirty_file(self):
        """The log counts notes sent, so Jake can watch the rate; a silent
        repeat adds no line."""
        path = self.prose_file("memo.md", "The estimand %s the estimate.\n" % EM_DASH)
        self.run_posttool("Write", {"file_path": path})
        self.run_posttool("Edit", {"file_path": path})
        self.assertEqual(len(self.records()), 1)

    def test_unwritable_state_still_reports_the_full_note(self):
        """Fail open: if the memory of past notes cannot be kept, report
        everything, as the gate did before it had a memory."""
        path = self.prose_file("memo.md", "The estimand %s the estimate.\n" % EM_DASH)
        state = sg.state_path(self.log)
        os.makedirs(os.path.dirname(state), exist_ok=True)
        os.makedirs(state)  # a directory where the file should be
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertIn("U+2014", self.context_of(out))
        _, again = self.run_posttool("Edit", {"file_path": path})
        self.assertIn("U+2014", self.context_of(again))


def transcript_file(directory, turns):
    """A session transcript as Claude Code writes it: one JSON record per
    line. `turns` is a list of ("user", text), ("assistant", text) or
    ("tool_result", text). Tool results are user records whose content is a
    tool_result block, which is text Jake never saw on his screen."""
    path = os.path.join(directory, "session.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for kind, text in turns:
            if kind == "user":
                rec = {"type": "user", "origin": {"kind": "human"},
                       "message": {"role": "user", "content": text}}
            elif kind == "assistant":
                rec = {"type": "assistant",
                       "message": {"role": "assistant", "content": [
                           {"type": "thinking", "thinking": "private"},
                           {"type": "text", "text": text},
                           {"type": "tool_use", "name": "Bash", "input": {}}]}}
            else:
                rec = {"type": "user",
                       "message": {"role": "user", "content": [
                           {"type": "tool_result", "content": text}]}}
            fh.write(json.dumps(rec) + "\n")
    return path


class TestCheck(GateCase):
    """The `check` entry point: the assistant runs it on a draft reply
    before sending. It runs the scanner, then hands the draft and what Jake
    has seen of the session to a second model that reads the draft one
    sentence at a time, and prints both sets of findings.

    Why a second model: the assistant that wrote "registry count" knows
    which registry and cannot see the word as a fault; Jake, who never saw
    the file, stops on it. Between 2026-09-14 and 2026-09-20 every one of
    the 55 objections Jake raised to a chat reply came after a reminder to
    self-check had been injected before the turn. Jake's own description of
    the fix, 2026-09-20: one agent writes, a second asks what each sentence
    means, and the reader needs the context Jake has, which is the
    conversation and not the files.

    The reader is injected so the tests stay offline. The real one calls
    `claude -p`.
    """

    def setUp(self):
        super().setUp()
        self.calls = []

    def fake_reader(self, prompt):
        self.calls.append(prompt)
        return json.dumps([{"sentence": "Two gaps.", "meaning": "CANNOT",
                            "verdict": "stop", "words": "Two gaps.",
                            "why": "No main verb."}])

    def draft(self, text):
        path = os.path.join(self._tmp.name, "draft.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def run_check(self, draft_path, transcript=None, reader=None):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.run_check(draft_path, self.log, transcript,
                                reader or self.fake_reader)
        return code, buf.getvalue()

    def test_scanner_findings_are_printed(self):
        path = self.draft("The estimand %s the estimate.\n" % EM_DASH)
        code, out = self.run_check(path)
        self.assertEqual(code, 0)
        self.assertIn("U+2014", out)

    def test_reader_findings_are_printed_with_the_offending_words(self):
        path = self.draft("Two gaps. A path is invisible.\n")
        _, out = self.run_check(path)
        self.assertIn("Two gaps.", out)
        self.assertIn("No main verb.", out)

    def test_reader_receives_the_draft(self):
        path = self.draft("Two gaps. A path is invisible.\n")
        self.run_check(path)
        self.assertEqual(len(self.calls), 1)
        self.assertIn("A path is invisible.", self.calls[0])

    def test_reader_receives_what_jake_saw_and_not_what_he_did_not(self):
        transcript = transcript_file(self._tmp.name, [
            ("user", "What is the registry count?"),
            ("assistant", "The registry holds twenty entries."),
            ("tool_result", "SECRET TOOL OUTPUT"),
        ])
        path = self.draft("Twenty, as before.\n")
        self.run_check(path, transcript=transcript)
        prompt = self.calls[0]
        self.assertIn("What is the registry count?", prompt)
        self.assertIn("The registry holds twenty entries.", prompt)
        self.assertNotIn("SECRET TOOL OUTPUT", prompt)
        self.assertNotIn("private", prompt)

    def test_jakes_turns_survive_a_run_of_assistant_status_lines(self):
        """The window is counted in Jake's turns, not in turns of either
        kind: in a long session the assistant writes many one-line status
        notes, and counting those pushed Jake's own words out (2026-09-20)."""
        turns = [("user", "What is the registry count?")]
        turns += [("assistant", "Still working, status %d." % i) for i in range(12)]
        transcript = transcript_file(self._tmp.name, turns)
        path = self.draft("Twenty.\n")
        self.run_check(path, transcript=transcript)
        self.assertIn("What is the registry count?", self.calls[0])

    def test_reader_is_asked_what_each_sentence_means(self):
        """Jake's specification of the second agent, 2026-09-20: for every
        sentence, what does it mean, and would the verbs still make sense if
        the nouns were swapped."""
        path = self.draft("A sentence.\n")
        self.run_check(path)
        prompt = self.calls[0].lower()
        self.assertIn("sentence by sentence", prompt)
        self.assertIn("what does this sentence mean", prompt)
        self.assertIn("nouns", prompt)

    def test_reader_prompt_names_no_banned_words(self):
        """The reader gets questions, not a word list; the list would make
        it flag the words and miss the habit, and the scanner already has
        the list."""
        path = self.draft("A sentence.\n")
        self.run_check(path)
        for word in ("load-bearing", "appropriate", "costs"):
            self.assertNotIn(word, self.calls[0])

    def test_reader_failure_leaves_the_scanner_findings_and_says_so(self):
        def broken(prompt):
            raise OSError("no network")
        path = self.draft("The estimand %s the estimate.\n" % EM_DASH)
        code, out = self.run_check(path, reader=broken)
        self.assertEqual(code, 0)
        self.assertIn("U+2014", out)
        self.assertIn("reader did not run", out.lower())

    def test_reader_returning_prose_instead_of_json_is_reported_as_not_run(self):
        path = self.draft("A sentence.\n")
        code, out = self.run_check(path, reader=lambda p: "Ready for the next question.")
        self.assertEqual(code, 0)
        self.assertIn("reader did not run", out.lower())

    def test_a_clean_draft_says_so_in_one_line(self):
        path = self.draft("The estimand differs from the estimate.\n")
        _, out = self.run_check(path, reader=lambda p: "[]")
        self.assertIn("nothing", out.lower())

    def test_check_records_the_draft_for_the_stop_hook(self):
        path = self.draft("The estimand differs from the estimate.\n")
        self.run_check(path, reader=lambda p: "[]")
        _, _ = self.run_stop("The estimand differs from the estimate.")
        rec = self.records()[-1]
        self.assertTrue(rec["checked"])


class TestPointOfTheProject(GateCase):
    """The reader is told what the project is for.

    Before 2026-10-15 the reader could ask only whether a passage states the
    question it answers. A passage that clearly answers a question the
    project does not need answered passed, because nothing the reader had
    said what the project needs. Each project now keeps POINT.md at its
    root: who reads the work, what they should believe or be able to do
    afterward, what difference it is meant to make, and what it does not
    claim. Jake confirms that file, which is why the reader may see it
    although it is not part of the conversation.

    The walk up from the working directory stops at the project root, the
    first directory holding .git, so that a POINT.md belonging to some other
    project above it is never read as this project's.
    """

    def setUp(self):
        super().setUp()
        self.calls = []
        self.proj = os.path.join(self._tmp.name, "proj")
        self.deep = os.path.join(self.proj, "Paper", "sections")
        os.makedirs(self.deep)
        os.makedirs(os.path.join(self.proj, ".git"))

    def capture(self, prompt):
        self.calls.append(prompt)
        return "[]"

    def write(self, path, text):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def draft(self, text="The estimand differs from the estimate.\n"):
        return self.write(os.path.join(self._tmp.name, "draft.md"), text)

    def check(self, point_path):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sg.run_check(self.draft(), self.log, None, self.capture,
                         point_path=point_path)
        return self.calls[-1]

    def test_point_file_is_found_from_a_subdirectory_of_the_project(self):
        point = self.write(os.path.join(self.proj, "POINT.md"), "x\n")
        self.assertEqual(sg.find_point_file(self.deep), point)

    def test_walk_stops_at_the_project_root(self):
        """A POINT.md above the directory holding .git belongs to something
        else."""
        self.write(os.path.join(self._tmp.name, "POINT.md"), "x\n")
        self.assertIsNone(sg.find_point_file(self.deep))

    def test_no_point_file_gives_none(self):
        self.assertIsNone(sg.find_point_file(self.deep))

    def test_point_text_reaches_the_reader(self):
        point = self.write(os.path.join(self.proj, "POINT.md"),
                           "Readers: methodologists choosing a test.\n")
        prompt = self.check(point)
        self.assertIn("Readers: methodologists choosing a test.", prompt)

    def test_without_a_point_the_reader_is_told_none_is_on_file(self):
        """The reader must not guess a point when Jake has confirmed none."""
        prompt = self.check(None)
        self.assertIn("no statement of the point", prompt.lower())

    def test_a_long_point_file_is_cut(self):
        """A statement of the point is a few sentences. A file far longer
        than that is cut so it cannot crowd out the conversation."""
        point = self.write(os.path.join(self.proj, "POINT.md"),
                           "word " * 10000)
        self.assertLessEqual(len(sg.read_point(point)), sg.POINT_CHARS)

    def test_check_takes_the_point_and_transcript_from_flags(self):
        """--point names a file directly, for a session whose working
        directory is outside the project."""
        draft, transcript, point = sg.parse_check_args(
            ["check", "d.md", "--transcript", "t.jsonl", "--point", "p.md"])
        self.assertEqual((draft, transcript, point),
                         ("d.md", "t.jsonl", "p.md"))
        self.assertEqual(sg.parse_check_args(["check", "d.md"]),
                         ("d.md", None, None))

    def test_check_says_which_point_file_the_reader_got(self):
        """A reader that found nothing and a reader never shown the point
        look the same from outside. The walk starts from the shell's working
        directory, so a check run after `cd` into the scratchpad finds no
        POINT.md. The output names the file, or says none was found and
        where the search started."""
        point = self.write(os.path.join(self.proj, "POINT.md"), "x\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sg.run_check(self.draft(), self.log, None, self.capture,
                         point_path=point)
        self.assertIn("Point: " + point, buf.getvalue())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sg.run_check(self.draft(), self.log, None, self.capture)
        self.assertIn("none on file", buf.getvalue())
        self.assertIn(os.getcwd(), buf.getvalue())

    def test_question_2_asks_what_the_passage_does_for_the_point(self):
        """The question measured on 2026-09-20 survives, and the reader is
        also asked to name the passage's job toward the stated point."""
        q = sg.QUESTIONS[1].lower()
        self.assertIn("what question it answers", q)
        self.assertIn("point", q)


class TestNewestTranscript(unittest.TestCase):
    """`check` finds the live session's transcript on its own, so the
    assistant has nothing to look up. Claude Code keeps one JSONL per
    session under ~/.claude/projects/<flattened cwd>/, where the flattening
    turns every character that is not a letter or a digit into a hyphen:
    /Users/jwbowers/repos/ai_workflow is -Users-jwbowers-repos-ai-workflow.
    The first version replaced only the slashes and found nothing for a
    directory with an underscore in its name (2026-09-20)."""

    def test_underscore_in_cwd_is_flattened_to_a_hyphen(self):
        with tempfile.TemporaryDirectory() as home:
            proj = os.path.join(home, ".claude", "projects",
                                "-Users-j-repos-ai-workflow")
            os.makedirs(proj)
            older = os.path.join(proj, "a.jsonl")
            newer = os.path.join(proj, "b.jsonl")
            for path in (older, newer):
                with open(path, "w") as fh:
                    fh.write("{}\n")
            os.utime(older, (1, 1))
            found = sg.newest_transcript("/Users/j/repos/ai_workflow", home)
            self.assertEqual(found, newer)

    def test_session_id_wins_over_the_newer_file(self):
        """Two sessions in one directory: the other session's file is newer,
        but the id names ours."""
        with tempfile.TemporaryDirectory() as home:
            proj = os.path.join(home, ".claude", "projects", "-Users-j-repos-x")
            os.makedirs(proj)
            mine = os.path.join(proj, "abc.jsonl")
            theirs = os.path.join(proj, "def.jsonl")
            for path in (mine, theirs):
                with open(path, "w") as fh:
                    fh.write("{}\n")
            os.utime(mine, (1, 1))
            self.assertEqual(sg.newest_transcript("/Users/j/repos/x", home, "abc"), mine)
            self.assertEqual(sg.newest_transcript("/Users/j/repos/x", home, None), theirs)

    def test_no_transcript_gives_none(self):
        with tempfile.TemporaryDirectory() as home:
            self.assertIsNone(sg.newest_transcript("/nowhere/at/all", home))


class TestHooksStaySilentInsideTheReader(GateCase):
    """The reader is a `claude -p` session on the same machine, with the
    same hooks. Its Stop hook wrote 40 "unchecked reply" lines to the log
    in one evening (2026-09-20), which would make the rate Jake watches
    meaningless. The reader is started with STYLE_GATE_READER set, and every
    hook entry point returns at once when it sees that."""

    def setUp(self):
        super().setUp()
        os.environ[sg.READER_MARK] = "1"

    def tearDown(self):
        os.environ.pop(sg.READER_MARK, None)
        super().tearDown()

    def test_stop_writes_nothing_inside_the_reader(self):
        code, out = self.run_stop("a %s b" % EM_DASH)
        self.assertEqual(code, 0)
        self.assertIsNone(out)
        self.assertEqual(self.records(), [])

    def test_preflight_injects_nothing_inside_the_reader(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sg.main(["preflight"], "", self.log)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_the_reader_process_gets_the_mark(self):
        """call_reader is not run here (it needs the network); the mark it
        sets is the one the entry points look for."""
        self.assertEqual(sg.READER_MARK, "STYLE_GATE_READER")


class TestStdinIsReadOnlyByHooks(unittest.TestCase):
    """The script reads its stdin for the hook events, which arrive there as
    JSON. `check` and `preflight` take nothing on stdin, and reading it
    anyway blocks forever when the assistant's shell keeps stdin open,
    which is what every live run of `check` did on 2026-09-20."""

    def test_hook_entry_points_read_stdin(self):
        self.assertTrue(sg.reads_stdin(["stop"]))
        self.assertTrue(sg.reads_stdin(["posttool"]))

    def test_check_and_preflight_do_not(self):
        self.assertFalse(sg.reads_stdin(["check", "draft.md"]))
        self.assertFalse(sg.reads_stdin(["preflight"]))
        self.assertFalse(sg.reads_stdin([]))

    def test_check_returns_when_stdin_never_closes(self):
        """Run the script as a process with a pipe on stdin that nothing
        writes to or closes. The reader is pointed at a transcript that does
        not exist and given no way to reach a model, so the only way this
        takes longer than a few seconds is the stdin read."""
        script = os.path.abspath(sg.__file__)
        with tempfile.TemporaryDirectory() as d:
            draft = os.path.join(d, "draft.md")
            with open(draft, "w") as fh:
                fh.write("A sentence.\n")
            # No `claude` on the path. CLAUDECODE=1 keeps the reader path in
            # play wherever the suite runs: since 2026-10-28 a shell without
            # it skips the reader (test_style_gate_outside_claude_code.py).
            env = dict(os.environ, PATH=d, CLAUDECODE="1")
            import subprocess
            proc = subprocess.Popen(
                [sys.executable, script, "check", draft, "--transcript",
                 os.path.join(d, "none.jsonl")],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, env=env)
            try:
                out, _ = proc.communicate(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()
                self.fail("check blocked on stdin")
            self.assertIn("Reader did not run", out)


class TestStopRecordsWhetherTheReplyWasChecked(GateCase):
    """Every reply with prose now gets one log record carrying `checked`:
    whether the reply the terminal showed is the draft that went through
    `check`. Jake asked on 2026-09-20 to stop having to ask whether the
    audit ran; the log answers instead. A reply edited after the check
    still counts when most of its sentences were in the checked draft.
    """

    def check_draft(self, text):
        path = os.path.join(self._tmp.name, "draft.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sg.run_check(path, self.log, None, lambda p: "[]")

    def test_unchecked_reply_is_recorded_as_unchecked(self):
        self.run_stop("A clean reply that nobody checked.")
        recs = self.records()
        self.assertEqual(len(recs), 1)
        self.assertFalse(recs[0]["checked"])

    def test_checked_reply_is_recorded_as_checked(self):
        self.check_draft("The estimand differs from the estimate. So does the rest.\n")
        self.run_stop("The estimand differs from the estimate. So does the rest.")
        self.assertTrue(self.records()[-1]["checked"])

    def test_a_lightly_edited_reply_still_counts_as_checked(self):
        self.check_draft("One sentence here. A second sentence here. A third one here. A fourth one here. A fifth one here.\n")
        self.run_stop("One sentence here. A second sentence here. A third one here. A fourth one here. A different fifth.")
        self.assertTrue(self.records()[-1]["checked"])

    def test_a_mostly_new_reply_does_not_count_as_checked(self):
        self.check_draft("One sentence here. A second sentence here.\n")
        self.run_stop("Something else entirely. And more of it. And a third thing. And a fourth.")
        self.assertFalse(self.records()[-1]["checked"])

    def test_a_clean_unchecked_reply_gets_no_note(self):
        """The record is for Jake's log; the assistant gets no nag, because
        a note after the fact cannot change the reply he already read."""
        _, out = self.run_stop("A clean reply that nobody checked.")
        self.assertIsNone(out)

    def test_clean_reply_record_carries_a_clean_tier(self):
        self.run_stop("A clean reply.")
        self.assertEqual(self.records()[0]["tier"], "clean")


class TestAuditBeforeAnswering(GateCase):
    """The note after a document is saved asks for the style audit before
    the reply, so the audit guard has nothing to ask for at the end.

    Jake chose this on 2026-10-26 (memo_audit_guard_in_focus_view_2026-10-26.md).
    When the guard asks for the audit after the reply, the model has to send
    the reply a second time, because focus view shows only the last message
    of a turn. An audit run before the reply means the reply goes out once.

    A document here is what audit_guard.py counts as one: a prose file
    outside the scratch area and outside ~/.claude. A reply draft in the
    scratch area has its own check, `style_gate.py check`, and a memory file
    under ~/.claude is not prose that leaves the desk, so neither is asked
    for the audit.
    """

    def setUp(self):
        super().setUp()
        self.home = os.path.join(self._tmp.name, "home")
        self.proj = os.path.join(self._tmp.name, "proj")
        self.scratch = os.path.join(self._tmp.name, "scratch")
        for d in (self.home, self.proj, self.scratch):
            os.makedirs(d)

    def save(self, folder, name, text):
        path = os.path.join(folder, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def run_posttool(self, path, session="s1"):
        event = json.loads(posttool_event("Write", {"file_path": path}))
        event["session_id"] = session
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.run_posttool(json.dumps(event), self.log,
                                   home=self.home,
                                   scratch_roots=(self.scratch,))
        self.assertEqual(code, 0)
        out = buf.getvalue().strip()
        return self.context_of(json.loads(out)) if out else None

    def asks_for_the_audit(self, note):
        text = (note or "").lower()
        return "style-audit" in text and "before you write to jake" in text

    def test_a_clean_document_is_asked_for_the_audit(self):
        """A clean scan says nothing about the eight questions the scan
        cannot answer, so a clean document needs the request most."""
        memo = self.save(self.proj, "memo.md", "The estimand is the average.\n")
        note = self.run_posttool(memo)
        self.assertTrue(self.asks_for_the_audit(note))
        self.assertIn("memo.md", note)

    def test_a_dirty_document_is_asked_for_the_audit_after_its_findings(self):
        memo = self.save(self.proj, "memo.md", "a %s b\n" % EM_DASH)
        note = self.run_posttool(memo)
        self.assertIn("unicode", note)
        self.assertTrue(self.asks_for_the_audit(note))

    def test_the_audit_is_asked_for_once_per_document_and_session(self):
        """The audit's own fixes are saves of the same file. Asking again
        after each one would send the model back into the audit it is
        finishing."""
        memo = self.save(self.proj, "memo.md", "a %s b\n" % EM_DASH)
        self.run_posttool(memo)
        self.assertIsNone(self.run_posttool(memo))
        with open(memo, "a", encoding="utf-8") as fh:
            fh.write("\nThe design is appropriate here.\n")
        later = self.run_posttool(memo)
        self.assertIn("appropriate", later)
        self.assertFalse(self.asks_for_the_audit(later))

    def test_a_document_reached_through_a_link_is_asked_once(self):
        """In this repository skills/ is a link to plugins/ai-workflow/skills,
        so one file has two names. On 2026-10-26 the note asked for the
        audit of style-audit's SKILL.md under each name in one session."""
        real = os.path.join(self.proj, "plugins", "skills")
        os.makedirs(real)
        os.symlink(real, os.path.join(self.proj, "skills"))
        self.save(real, "SKILL.md", "A clean skill.\n")
        self.assertTrue(self.asks_for_the_audit(
            self.run_posttool(os.path.join(real, "SKILL.md"))))
        self.assertIsNone(self.run_posttool(
            os.path.join(self.proj, "skills", "SKILL.md")))

    def test_another_session_is_asked_again(self):
        memo = self.save(self.proj, "memo.md", "The estimand is the average.\n")
        self.run_posttool(memo, session="s1")
        self.assertTrue(self.asks_for_the_audit(
            self.run_posttool(memo, session="s2")))

    def test_a_reply_draft_in_the_scratch_area_is_not_asked(self):
        clean = self.save(self.scratch, "reply.md", "A clean draft.\n")
        self.assertIsNone(self.run_posttool(clean))
        dirty = self.save(self.scratch, "reply2.md", "a %s b\n" % EM_DASH)
        note = self.run_posttool(dirty)
        self.assertIn("unicode", note)
        self.assertFalse(self.asks_for_the_audit(note))

    def test_a_file_under_dot_claude_is_not_asked(self):
        mem = self.save(os.path.join(self.home, ".claude", "memory"),
                        "fact.md", "A clean memory.\n")
        self.assertIsNone(self.run_posttool(mem))

    def test_the_gate_and_the_guard_agree_on_what_a_document_is(self):
        """If the note asked for the audit on a file the guard ignores, or
        the reverse, the guard would fire after a reply the note had tried
        to make safe."""
        import audit_guard as ag
        paths = [os.path.join(self.proj, "memo.md"),
                 os.path.join(self.scratch, "reply.md"),
                 os.path.join(self.home, ".claude", "memory", "fact.md"),
                 os.path.join(self.proj, "gate.py")]
        for p in paths:
            self.assertEqual(
                sg.is_document(p, self.home, (self.scratch,)),
                ag.is_document(p, self.home, (self.scratch,)), p)

    def test_the_request_is_plain_ascii(self):
        memo = self.save(self.proj, "memo.md", "The estimand is the average.\n")
        self.assertTrue(all(ord(c) <= 126 for c in self.run_posttool(memo)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
