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
    judgment, so only it belongs in the injected rules. "costs" is usually
    literal, and banning the word would train avoidance of an item instead
    of the habit.

  * IT FAILS OPEN AND SILENT. Malformed JSON, a missing field, a raised
    exception: exit 0, no log line, no output. Losing one measurement is a
    smaller loss than a broken session.

Fenced code is skipped, reusing style_scan's fence handling: Claude shows
shell and R constantly, and 'sandbox', 'pipeline' and 'costs' are ordinary
words there.

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
        """It rides on every single turn, so length is not free."""
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertLess(len(ctx), 600)


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


class TestTierMembershipIsOneLine(unittest.TestCase):
    """If the judgment tier should ever be treated as mechanical, that is a
    one-line edit to a constant, not a change spread through the code."""

    def test_mechanical_categories_declared_in_one_place(self):
        self.assertEqual(set(sg.MECHANICAL),
                         {"unicode", "bold-run-in-opener", "dash-semicolon"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
