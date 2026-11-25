#!/usr/bin/env python3

# What this file is for
# ---------------------
#
# This file tests the script style_gate.py. The script helps Claude follow
# Jake's writing rules. These tests check that the script does what Jake
# wants it to do.
#
# To run the tests, type this in the top folder of the repository:
#
#     make test-style-gate
#
#
# What style_gate.py does
# -----------------------
#
# The script has four commands. Claude Code runs the first three by itself,
# at set times. Claude runs the fourth one.
#
#   preflight   Claude Code runs this when Jake sends a message. The command
#               prints a short reminder about the writing rules. Claude reads
#               the reminder before starting a reply.
#
#   stop        Claude Code runs this when Claude finishes a reply. The
#               command looks for faults in the reply. Then the command adds
#               a line about the reply to a file called the log.
#
#   posttool    Claude Code runs this after Claude uses a tool that can save
#               a file. The command looks for faults in the saved file. If
#               the command finds faults that it has not told Claude about, it
#               sends Claude a list of them.
#
#   check       Claude runs this on a draft before sending the draft to Jake.
#               The command looks for faults in the draft. Then it asks a
#               second AI model to read the draft as Jake would read it.
#
#
# Words this file uses
# --------------------
#
# The script is style_gate.py.
#
# The scanner is another script, style_scan.py. It finds words and
# punctuation that may break Jake's writing rules. style_gate.py uses the
# scanner.
#
# The reader is the second AI model. It reads a draft for the check command.
#
# A fault is one place that the scanner reports. Some faults break a rule.
# Other faults only need a person to look at them.
#
# Clean text is text in which the scanner finds no faults. Some names below
# use the word "dirty" for text with a fault.
#
# A note is words that the script prints for Claude to read.
#
# The log is a file. The script adds one line to it for each reply the
# script looks at. The script also adds a line when it sends a note about a
# file. Each line of the log is called a record. Jake uses the log to see
# how often Claude breaks a rule.
#
# A tier is one word in a record. It says which group of faults the script
# found. The groups are described below. One more tier, "unchecked", means
# that the scanner did not read the file.
#
# A tool is something Claude can use to do a job. Write saves a file. Edit
# changes a file. Bash runs a terminal command.
#
# A hook is a command that Claude Code runs by itself at a set time. The
# preflight, stop, and posttool commands are hooks.
#
# An event is what Claude Code tells a hook when it runs the hook. For the
# stop command, the event holds the words of Claude's reply.
#
# JSON is a way to write data as plain text. Events and records are in JSON.
#
# A session is one conversation between Jake and Claude.
#
# A transcript is the file in which Claude Code keeps a session.
#
# A path is the full name of a file or folder. It starts with the folders
# that the file is in. For example, /Users/j/repos/memo.md is a path.
#
# A prose file is a file that holds writing meant for people. The script
# decides by the end of the file's name. Names that end in .md or .tex are
# examples.
#
# A terminal command is a line that someone types in the terminal, such as
# "ls".
#
# A skill is a set of instructions that Claude can load.
#
# The eight questions are in the style-audit skill. The reader asks them
# about a draft.
#
# ASCII is the set of characters on a plain keyboard. Python gives each
# character a number. The numbers of the ASCII characters go up to 126. Jake
# wants only these characters in text that Claude writes. All other
# characters are called unicode in this file.
#
#
# Three kinds of faults
# ---------------------
#
# The scanner sorts the faults it finds into named kinds. style_gate.py puts
# those kinds into three groups.
#
# Mechanical faults are ones that a computer can be sure about. There are
# three kinds.
#
#     unicode                a character that is not ASCII
#     bold-run-in-opener     a line that opens with a bold sentence
#     dash-semicolon         a line with both --- and a semicolon
#
# Jake types --- for a long dash.
#
# Judgment faults are ones that a person has to decide about. For example,
# the scanner reports the word `costs`. Jake does not want that word in a
# sentence such as "this costs us clarity." The word is fine when the sentence
# is about money. The scanner cannot tell which one the writer meant.
#
# Attention faults only ask for a second look. There is one kind, called
# trailing-clause. An example is a sentence that goes on after a comma with
# the word "which".
#
# The tier in a record about a reply is one of three words. The tier is
# "mechanical" when the reply has a mechanical fault. It is "judgment" when the
# reply has only other faults. It is "clean" when the reply has no faults.
#
#
# How to read the Python
# ----------------------
#
# A line that starts with # is a comment. Python skips it. Comments are for
# people. Two of them are for other programs. One is the first line of this
# file. The other is "noqa: E402" below.
#
# A line that starts with "def" begins a function. A function is a set of
# steps with a name. A function whose name starts with "test_" is a test.
#
# A line that starts with "class" begins a group of functions. Most of these
# groups hold tests about one question. The question is in the comment above
# the group.
#
# A class can be built on another class. "class TestLogging(GateCase)" means
# that TestLogging can use everything in GateCase.
#
# A function named setUp runs before each test in its group. A function named
# tearDown runs after each test.
#
# A test makes one or more claims. Python has a word for each kind of claim.
# If any claim is false, the test fails. "None" is Python's word for "nothing
# is here." Here are the claims in this file:
#
#     self.assertEqual(x, y)           x and y are the same
#     self.assertTrue(x)               x is true
#     self.assertFalse(x)              x is false
#     self.assertIn(x, y)              x is somewhere in y
#     self.assertNotIn(x, y)           x is nowhere in y
#     self.assertIsNone(x)             x is None
#     self.assertIsNotNone(x)          x is not None
#     self.assertGreater(x, y)         x is larger than y
#     self.assertLess(x, y)            x is smaller than y
#     self.assertLessEqual(x, y)       x is smaller than y or equal to y
#
# The word "self" means the group that the test is in. So self.run_stop is
# the function run_stop in that group, or in the class it is built on.
#
# In "a %s b" % EM_DASH, Python puts the long dash where the %s is.
#
# In "code, out = self.run_stop(...)", run_stop gives back two things. Python
# names the first one "code" and the second one "out". When a test does not
# need one of them, the test can name it "_".
#
# "code" is the number that a command gives back when it ends. This script
# should always give back zero.
#
# "out" is what the script printed. For a hook, "out" is JSON with the note
# inside it. The function context_of takes the note out of the JSON. When a
# hook prints nothing, "out" is None. For the check command, "out" is plain
# text.
#
# In "def draft(self, text)", the words in parentheses stand for things that
# the function is given. So "text" is whatever text a test gives to draft.
#
# records()[0] is the first record in the log. records()[-1] is the last one.
# records()[0]["tier"] is the tier in the first record.
#
# A comment that starts with a word such as "Run" or "Make" says what Python
# does. You do not have to do anything.
#
# Claude does not run in these tests. "Claude saves a file" means that the test
# saves the file and then tells the script that Claude saved it. Terminal
# commands do not run either. A test only tells the script about them.
#
# Some sample sentences in the tests are bad on purpose, so that the scanner
# has something to find.
#
# This file has only ASCII characters, because Jake's rule covers it too. So
# the long dash is written as "\u2014". Python reads that as the long dash.

import contextlib
import io
import json
import os
import sys
import tempfile
import time
import unittest

# These lines tell Python where style_gate.py is. After them, "sg" means
# style_gate.py. For example, sg.main is the function named main in that
# script.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
import style_gate as sg  # noqa: E402

# EM_DASH is the long dash.
EM_DASH = "\u2014"

# EN_DASH is a shorter dash. People use it between page numbers.
EN_DASH = "\u2013"


# This function makes a fake event for the stop command. The fake event has
# the parts of a real event that the stop command reads. "message" is the
# reply that Claude just finished. "prompt_id" is a name for the message from
# Jake that Claude was answering.
def stop_event(message, prompt_id="p1"):
    return json.dumps({"hook_event_name": "Stop",
                       "prompt_id": prompt_id,
                       "session_id": "s1",
                       "last_assistant_message": message})


# Most groups of tests below are built on this class. It holds the tools they
# share.
class GateCase(unittest.TestCase):

    # Before each test, make an empty folder that will be thrown away later.
    # Choose a path for the log inside that folder. Then the tests never touch
    # Jake's real log. The path goes through a second folder, named "sub". The
    # folder "sub" does not exist yet. The script has to make it.
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.log = os.path.join(self._tmp.name, "sub", "style_gate.jsonl")

    # After each test, throw the folder away.
    def tearDown(self):
        self._tmp.cleanup()

    # Run the stop command on a message. Catch whatever the command prints.
    # Give back "code" and "out".
    def run_stop(self, message, prompt_id="p1"):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["stop"], stop_event(message, prompt_id), self.log)
        out = buf.getvalue().strip()
        return code, (json.loads(out) if out else None)

    # Read every record in the log. If there is no log yet, give back an
    # empty list.
    def records(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as fh:
            return [json.loads(ln) for ln in fh if ln.strip()]

    # Take the words of a note out of the JSON that the script printed.
    def context_of(self, payload):
        return payload["hookSpecificOutput"]["additionalContext"]


# Can the stop command keep Claude from ever finishing?
#
# If the stop command gave back the number 2, Claude Code would make Claude
# keep going. Claude would write another message. The stop command would run
# again on that message. This could go on and on. So the stop command must
# always give back zero, even when the reply has faults.
class TestNeverBlocks(GateCase):

    # Run the stop command on a clean reply. It must give back zero.
    def test_clean_message_returns_zero(self):
        code, _ = self.run_stop("The estimand is the average treatment effect.")
        self.assertEqual(code, 0)

    # Run the stop command on a reply with a long dash in it. A long dash is a
    # mechanical fault. The command must still give back zero.
    def test_mechanical_violation_returns_zero(self):
        code, _ = self.run_stop("The estimand %s not the estimate." % EM_DASH)
        self.assertEqual(code, 0)

    # Run the stop command on a reply with a judgment fault, the word `costs`.
    # The command must still give back zero.
    def test_judgment_candidate_returns_zero(self):
        code, _ = self.run_stop("Running it on the cluster costs three days.")
        self.assertEqual(code, 0)

    # Run the stop command three times on the same reply. The reply has a
    # fault. The command must give back zero each time.
    def test_repeated_identical_dirty_messages_return_zero(self):
        dirty = "a %s b" % EM_DASH
        for _ in range(3):
            code, _ = self.run_stop(dirty)
            self.assertEqual(code, 0)


# Does the stop command write down what it finds?
#
# Each record in the log has a "tier" and "categories". The categories are
# the kinds of faults in the reply.
class TestLogging(GateCase):

    # A reply with a long dash must add one record. The record must say
    # "mechanical". It must list the kind of fault called "unicode".
    def test_mechanical_violation_is_logged_with_tier_and_category(self):
        self.run_stop("The estimand %s not the estimate." % EM_DASH)
        recs = self.records()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["tier"], "mechanical")
        self.assertIn("unicode", recs[0]["categories"])

    # The shorter dash is not ASCII either. The record must list the kind of
    # fault called "unicode".
    def test_en_dash_is_logged(self):
        self.run_stop("See pages 97%s124." % EN_DASH)
        self.assertIn("unicode", self.records()[0]["categories"])

    # This reply opens with a bold sentence. In Markdown, words between ** and
    # ** are bold. The record must list the kind of fault called
    # "bold-run-in-opener".
    def test_bold_run_in_opener_is_logged(self):
        self.run_stop("**What it gives up.** Three things.")
        self.assertIn("bold-run-in-opener", self.records()[0]["categories"])

    # This line has both --- and a semicolon. The record must list the kind of
    # fault called "dash-semicolon".
    def test_dash_semicolon_is_logged(self):
        self.run_stop("The test is exact --- it permutes; the bound is not.")
        self.assertIn("dash-semicolon", self.records()[0]["categories"])

    # A reply whose only fault is a judgment fault must get the tier
    # "judgment".
    def test_judgment_only_violation_logs_the_judgment_tier(self):
        self.run_stop("Clustering at the school level is appropriate.")
        self.assertEqual(self.records()[0]["tier"], "judgment")

    # This reply has two faults. The word `costs` is a judgment fault. The
    # long dash is a mechanical fault. The record can hold only one tier. It
    # must be "mechanical", because a computer can be sure about that fault.
    def test_both_tiers_logs_as_mechanical(self):
        self.run_stop("It costs three days %s more than we have." % EM_DASH)
        self.assertEqual(self.records()[0]["tier"], "mechanical")

    # A clean reply must also add one record to the log. The record's list of
    # faults must be empty. Jake wants to know for what share of all replies
    # Claude ran the check command first. To count that, the log needs the
    # clean replies as well.
    def test_clean_message_writes_one_record_with_no_categories(self):
        self.run_stop("The estimand is the average treatment effect.")
        recs = self.records()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["categories"], [])

    # Run the stop command on two replies. The log must then have two
    # records. This shows that the second record did not erase the first.
    def test_records_append_rather_than_overwrite(self):
        self.run_stop("a %s b" % EM_DASH, prompt_id="p1")
        self.run_stop("c %s d" % EM_DASH, prompt_id="p2")
        self.assertEqual(len(self.records()), 2)

    # This reply has two long dashes. The record must count two faults. The
    # record must also hold the name of the session. The fake event gave the
    # session the name "s1".
    def test_record_carries_a_count_and_a_session_id(self):
        self.run_stop("a %s b %s c" % (EM_DASH, EM_DASH))
        rec = self.records()[0]
        self.assertEqual(rec["count"], 2)
        self.assertEqual(rec["session_id"], "s1")

    # The folder for the log does not exist at first. The test checks that.
    # Then the test runs the stop command. The log must exist afterward. The
    # script cannot make the log without making the folder first.
    def test_missing_log_directory_is_created(self):
        self.assertFalse(os.path.exists(os.path.dirname(self.log)))
        self.run_stop("a %s b" % EM_DASH)
        self.assertTrue(os.path.exists(self.log))


# Can the stop command hide one of Claude's replies from Jake?
#
# The stop command used to do this. When the command found a fault in a reply,
# it sent Claude a note. Claude Code then had Claude write one more message.
# Jake uses a setting called focus mode. It shows only the last message that
# Claude writes before Jake types again. So the extra message took the place
# of the reply.
#
# From 2026-10-27 to 2026-11-24 this note went out 117 times. In 45 of those
# cases, the last message was less than half as long as the reply it
# replaced. Some of those messages were only "Understood." or "Noted."
#
# On 2026-11-24 Jake asked Claude to fix this. So now the stop command must
# print nothing. The command must still write in the log.
class TestStopSaysNothing(GateCase):

    # These are five replies with faults. Each of the first three has a
    # mechanical fault. Each of the last two has a judgment fault. The fifth
    # has the word `load-bearing` in it. That word led the script to hide a
    # reply from Jake on 2026-11-24.
    DIRTY = ("The estimand %s not the estimate." % EM_DASH,
             "**What it gives up.** Three things.",
             "The test is exact --- it permutes; the bound is not.",
             "Clustering at the school level is appropriate.",
             "The assumption is load-bearing.")

    # Run the stop command on a message. Give back everything it printed.
    def stdout_of(self, message):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sg.main(["stop"], stop_event(message), self.log)
        return buf.getvalue()

    # Go through the five replies one at a time. The stop command must print
    # nothing about any of them. In Python, "" means text with nothing in it.
    def test_a_dirty_reply_prints_nothing(self):
        for message in self.DIRTY:
            with self.subTest(message=message):
                self.assertEqual(self.stdout_of(message), "")

    # The stop command must also print nothing about a clean reply.
    def test_a_clean_reply_prints_nothing(self):
        self.assertEqual(
            self.stdout_of("The estimand is the average treatment effect."), "")

    # Go through the five replies again. After each one, the log must have
    # one more record. That record must count at least one fault. This shows
    # that the command still writes in the log.
    def test_a_dirty_reply_is_still_logged(self):
        for n, message in enumerate(self.DIRTY, 1):
            self.stdout_of(message)
            recs = self.records()
            self.assertEqual(len(recs), n)
            self.assertGreater(recs[-1]["count"], 0)

    # Another script, audit_guard.py, can have Claude write one more message.
    # When that happens, Claude Code runs the stop command a second time. Claude
    # Code marks the second event with "stop_hook_active". The stop command must
    # print nothing that time too.
    def test_a_second_stop_in_the_same_turn_prints_nothing(self):
        event = json.loads(stop_event(self.DIRTY[0]))
        event["stop_hook_active"] = True
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sg.main(["stop"], json.dumps(event), self.log)
        self.assertEqual(buf.getvalue(), "")


# Does the script skip computer code inside a reply?
#
# Claude often shows Jake some code. In a reply, the code goes between two
# lines that start with three backquotes: ```. Each of those two lines is
# called a fence. The first fence opens the code. The second fence closes it.
# Words such as `sandbox` are normal in code. So the script must not call
# these words faults when they are between the fences.
class TestFencedCodeIsSkipped(GateCase):

    # This reply has three words that the scanner would report. All three are
    # between the fences. The stop command must give back zero. The command
    # must print nothing. The record must list no faults.
    def test_offenders_only_inside_a_fence_are_ignored(self):
        msg = ("Here is the command:\n\n```bash\n"
               "# costs and pipeline and sandbox\nrun --sandbox\n```\n")
        code, out = self.run_stop(msg)
        self.assertEqual(code, 0)
        self.assertIsNone(out)
        self.assertEqual(self.records()[0]["categories"], [])

    # This reply has a long dash before the first fence. The record must list
    # that fault.
    def test_prose_offender_beside_a_fence_is_caught(self):
        msg = "The estimand %s below.\n\n```r\nx <- 1  # costs\n```\n" % EM_DASH
        self.run_stop(msg)
        self.assertIn("unicode", self.records()[0]["categories"])

    # This reply has a fence that opens the code but no fence that closes it.
    # The stop command must still finish. The command must give back zero.
    def test_unclosed_fence_terminates_without_raising(self):
        code, _ = self.run_stop("```bash\nrun\n")
        self.assertEqual(code, 0)


# Can Claude tell Jake which word was a fault without making a new fault?
#
# On 2026-09-01 the script found a fault in a reply. In its next reply, Claude
# told Jake which word it was. The script counted that word as a second
# fault. So one fault was counted twice. Now Claude can put the word between
# single backquotes, like `this`. The script must skip words written that way.
class TestInlineCodeIsSkipped(GateCase):

    # The scanner reports `lands` in normal text. Here the word is between
    # backquotes. The function scan_message looks for faults in a reply. It
    # must give back an empty list. In Python, [] is an empty list.
    def test_offender_between_code_marks_is_not_a_finding(self):
        self.assertEqual(sg.scan_message("the pattern for `lands` fired"), [])

    # This reply names two words between backquotes. The stop command must
    # print nothing. The record must list no faults. The record's tier must be
    # "clean".
    def test_a_report_of_a_finding_logs_no_fault(self):
        code, out = self.run_stop(
            "The scanner caught `lands` and `costs` in the last reply.")
        self.assertEqual(code, 0)
        self.assertIsNone(out)
        self.assertEqual(self.records()[0]["categories"], [])
        self.assertEqual(self.records()[0]["tier"], "clean")

    # Here the same two words are in normal text, with no backquotes. The
    # record must list the kind of fault called "idiom". An idiom is a saying
    # that does not mean what its words say. Nothing really falls to the ground
    # when people say that an argument `lands`.
    def test_the_same_words_in_prose_still_log(self):
        self.run_stop("The argument lands and the delay costs us a week.")
        recs = self.records()
        self.assertEqual(len(recs), 1)
        self.assertIn("idiom", recs[0]["categories"])


# Does the reminder say the right things?
#
# The preflight command prints a reminder when Jake sends a message. Claude
# reads the reminder before Claude writes a reply. So the reminder can help
# Claude avoid a fault.
class TestPreflight(unittest.TestCase):

    # Run the preflight command with a fake message from Jake. Give back "code"
    # and "out". The reminder is inside "out".
    def run_preflight(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["preflight"], json.dumps(
                {"hook_event_name": "UserPromptSubmit", "prompt": "hi"}), None)
        return code, json.loads(buf.getvalue())

    # The command must give back zero.
    def test_returns_zero(self):
        code, _ = self.run_preflight()
        self.assertEqual(code, 0)

    # The script prints the reminder inside some JSON. The JSON must also hold
    # the name UserPromptSubmit. That is Claude Code's name for "Jake sent a
    # message."
    def test_envelope_names_the_right_event(self):
        _, out = self.run_preflight()
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"],
                         "UserPromptSubmit")

    # The reminder must name all three mechanical faults. The code changes
    # the reminder to small letters first, so capital letters do not matter.
    def test_names_all_three_mechanical_rules(self):
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"].lower()
        self.assertIn("unicode", ctx)
        self.assertIn("bold", ctx)
        self.assertIn("semicolon", ctx)

    # The reminder must not name words that are judgment faults. If the
    # reminder named them, Claude would avoid those words but make the same
    # mistake with other words. The test checks that three such words are not
    # in the reminder.
    def test_does_not_name_judgment_categories(self):
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"].lower()
        for word in ("costs", "appropriate", "load-bearing"):
            self.assertNotIn(word, ctx)

    # Every character in the reminder must be ASCII. In Python, ord(c) is the
    # number of the character c. Each number must be 126 or less.
    def test_injection_is_pure_ascii(self):
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertTrue(all(ord(c) <= 126 for c in ctx))

    # The reminder must have fewer than 900 characters. Claude has to read it
    # each time Jake sends a message. The reminder used to hold the eight
    # questions that the reader now asks. It held them for six days. In those
    # six days Jake still objected to 55 replies. The questions had not
    # stopped the faults. On 2026-09-20 Claude took the questions out of the
    # reminder.
    def test_injection_is_short(self):
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertLess(len(ctx), 900)

    # The reminder must tell Claude to write its draft in a file. The reminder
    # must also give the whole check command, so that Claude does not have to
    # look it up. The test looks for three things in the reminder: the words
    # "style_gate.py check", the path of the script, and the word "file".
    def test_tells_claude_to_write_the_draft_to_a_file_and_check_it(self):
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("style_gate.py check", ctx)
        self.assertIn(os.path.abspath(sg.__file__), ctx)
        self.assertIn("file", ctx.lower())

    # The reminder must tell Claude to answer Jake's question. It must also
    # tell Claude to say what it needs from Jake. The code joins the lines of
    # the reminder into one line, so that a line break cannot split a phrase.
    def test_says_to_open_with_the_answer_and_what_is_needed(self):
        _, out = self.run_preflight()
        ctx = " ".join(out["hookSpecificOutput"]["additionalContext"].lower().split())
        self.assertIn("answer", ctx)
        self.assertIn("need from him", ctx)

    # The reminder must tell Claude to say what Jake wants the answer for.
    # Jake asked for this on 2026-10-15.
    def test_says_to_open_with_what_the_question_is_for(self):
        _, out = self.run_preflight()
        ctx = " ".join(out["hookSpecificOutput"]["additionalContext"].lower().split())
        self.assertIn("wants it for", ctx)

    # The reminder must not hold any of the eight questions. The test takes
    # three words and one phrase from those questions. It checks that they are
    # not in the reminder.
    def test_names_no_reading_question(self):
        _, out = self.run_preflight()
        ctx = out["hookSpecificOutput"]["additionalContext"].lower()
        for ph in ("pronoun", "antecedent", "therefore", "adds nothing"):
            self.assertNotIn(ph, ctx)

    # The eight questions are written down in two places. One is the script.
    # The other is section 0 of SKILL.md, the instructions for the style-audit
    # skill. Someone could add a question in one place but forget the other.
    # This test counts the questions in both places. Both counts must be 8.
    #
    # The code copies section 0 from SKILL.md. SKILL.md does not change. Then
    # the code counts the lines in the copy that start with a number and bold
    # words, such as "1. **Is every".
    def test_question_count_matches_skill_section_0(self):
        skill = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "SKILL.md")
        with open(skill, encoding="utf-8") as fh:
            text = fh.read()
        section = text.split("## 0.", 1)[1].split("## 1.", 1)[0]
        in_skill = sum(1 for ln in section.splitlines()
                       if ln[:1].isdigit() and ". **" in ln[:6])
        self.assertEqual(in_skill, 8)
        self.assertEqual(len(sg.QUESTIONS), in_skill)

    # None of the eight questions may quote a word. A question that quoted a
    # word would teach the reader to look for that one word. The test checks
    # that no question has a quotation mark in it.
    def test_questions_name_no_particular_words(self):
        for q in sg.QUESTIONS:
            self.assertNotIn('"', q, "this question quotes a word: " + q)


# What happens when something goes wrong?
#
# The script runs during Jake's work with Claude. If the script breaks, Jake's
# work must go on. So the script must give back zero even when something goes
# wrong.
class TestFailsOpen(GateCase):

    # An event should be JSON. This event is broken. The stop command must give
    # back zero. The command must print nothing. The command must add nothing
    # to the log.
    def test_malformed_json_exits_zero_and_silent(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["stop"], "{not json at all", self.log)
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")
        self.assertEqual(self.records(), [])

    # This event does not hold Claude's reply. The stop command must give back
    # zero.
    def test_missing_message_field_exits_zero(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["stop"], json.dumps({"hook_event_name": "Stop"}),
                           self.log)
        self.assertEqual(code, 0)

    # These replies have no words. The first one is empty. The second has
    # only spaces and line breaks. In Python, "\n" is a line break. The stop
    # command must give back zero for both replies. The command must print
    # nothing about them.
    def test_empty_and_whitespace_messages_exit_zero(self):
        for msg in ("", "   \n\n  "):
            code, out = self.run_stop(msg)
            self.assertEqual(code, 0)
            self.assertIsNone(out)

    # Here the test breaks the script on purpose. It puts a broken function
    # in place of scan_message. The stop command must give back zero anyway.
    # The command must print nothing. At the end, the test puts the real
    # function back, so that the other tests still work.
    def test_scan_failure_exits_zero(self):
        def broken(_text):
            raise RuntimeError("boom")
        original = sg.scan_message
        sg.scan_message = broken
        try:
            code, out = self.run_stop("a %s b" % EM_DASH)
        finally:
            sg.scan_message = original
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    # Here the script cannot write its log. The test makes a plain file named
    # "blocker". Then the test tells the script to put the log inside
    # "blocker", as if "blocker" were a folder. That cannot work. The stop
    # command must still give back zero.
    def test_unwritable_log_still_exits_zero(self):
        blocker = os.path.join(self._tmp.name, "blocker")
        open(blocker, "w").close()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["stop"], stop_event("a %s b" % EM_DASH),
                           os.path.join(blocker, "style.jsonl"))
        self.assertEqual(code, 0)

    # The test asks the script to run a command named "wat". The script has no
    # such command. The script must give back zero. The script must print
    # nothing.
    def test_unknown_subcommand_exits_zero_and_silent(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["wat"], "{}", self.log)
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")


# This function makes a fake event for the posttool command. "tool_name" is
# the tool that Claude used. Write and Edit are tools that save a file. Bash is
# a tool that runs a terminal command. A terminal command can also save a file.
# "tool_input" says what Claude did with the tool.
def posttool_event(tool_name, tool_input):
    return json.dumps({"hook_event_name": "PostToolUse",
                       "session_id": "s1",
                       "tool_name": tool_name,
                       "tool_input": tool_input,
                       "tool_response": {}})


# Does the script look for faults in the files that Claude saves?
#
# The stop command looks only at Claude's replies. It does not look at files.
# On 2026-09-14 Jake asked for Claude's documents to be checked without his
# having to ask each time. So the posttool command looks at each prose file
# that Claude saves. If the command finds faults that it has not told Claude
# about, it sends Claude a note. Then Claude can fix the file before telling
# Jake that the file is done.
#
# The test folder is a temporary folder. In a temporary folder, the script
# sends a note only about faults. The last group in this file tests another
# kind of note. That note asks Claude to use the style-audit skill.
class TestPostTool(GateCase):

    PROSE_EXTENSIONS = (".md", ".tex", ".Rmd", ".qmd", ".txt")

    # Make a file with this name and this text in the test folder. Give back
    # the path of the file.
    def prose_file(self, name, text):
        path = os.path.join(self._tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    # Run the posttool command. Give back "code" and "out".
    def run_posttool(self, tool_name, tool_input):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], posttool_event(tool_name, tool_input),
                           self.log)
        out = buf.getvalue().strip()
        return code, (json.loads(out) if out else None)

    # Claude saves a file with a long dash in it. The posttool command must
    # give back zero. The note must name the file. The note must also name the
    # kind of fault. The script prints the note inside some JSON. The JSON must
    # hold the name PostToolUse. That is Claude Code's name for "Claude just
    # used a tool."
    def test_write_of_a_dirty_md_file_injects_a_note_naming_the_file(self):
        path = self.prose_file("memo.md", "The estimand %s not the estimate.\n" % EM_DASH)
        code, out = self.run_posttool("Write", {"file_path": path, "content": "x"})
        self.assertEqual(code, 0)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PostToolUse")
        ctx = self.context_of(out)
        self.assertIn("memo.md", ctx)
        self.assertIn("unicode", ctx)

    # Make one file of each type in the list PROSE_EXTENSIONS. The first one is
    # draft.md. Each file has a long dash in it. The script must send a note
    # about each file.
    def test_each_prose_extension_is_scanned(self):
        for ext in self.PROSE_EXTENSIONS:
            path = self.prose_file("draft" + ext, "a %s b\n" % EM_DASH)
            _, out = self.run_posttool("Edit", {"file_path": path})
            self.assertIsNotNone(out, "the script did not scan " + ext)

    # A file named draft.RMD is the same type as draft.Rmd. The script must
    # send a note about it too.
    def test_extension_case_does_not_matter(self):
        path = self.prose_file("draft.RMD", "a %s b\n" % EM_DASH)
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertIsNotNone(out)

    # A .py file holds Python code. It is not a prose file. This one has a long
    # dash in it. The script must say nothing about the file.
    def test_a_code_file_is_ignored(self):
        path = self.prose_file("gate.py", "# a %s b\n" % EM_DASH)
        code, out = self.run_posttool("Write", {"file_path": path})
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    # The script must say nothing about a clean file.
    def test_a_clean_file_is_silent(self):
        path = self.prose_file("memo.md", "The estimand is the average treatment effect.\n")
        code, out = self.run_posttool("Write", {"file_path": path})
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    # This file has the word `costs` in some code between two fences. The
    # script must say nothing about the word.
    def test_fenced_code_in_markdown_is_skipped(self):
        path = self.prose_file("memo.md", "Run this:\n\n```r\nx <- 1  # costs\n```\n")
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertIsNone(out)

    # This file has a judgment fault, the words `is appropriate`. The scanner's
    # name for this kind of fault is "vague-evaluative". The note must have
    # that name in it.
    def test_a_judgment_candidate_is_reported_too(self):
        path = self.prose_file("memo.md", "Clustering at the school level is appropriate.\n")
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertIn("vague-evaluative", self.context_of(out))

    # This file has an attention fault. The fault is the part that starts with
    # the comma. If the script sends a note, the note must not name that fault.
    # The script may also send no note at all.
    def test_attention_categories_stay_out_of_the_note(self):
        path = self.prose_file("memo.md", "We ran it, and the rest follows.\n")
        _, out = self.run_posttool("Write", {"file_path": path})
        if out is not None:
            self.assertNotIn("trailing-clause", self.context_of(out))

    # The long dash is on the third line of this file. The note must say "line
    # 3", so that Claude can find the fault.
    def test_note_names_the_line_number(self):
        path = self.prose_file("memo.md", "clean\nclean\na %s b\n" % EM_DASH)
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertIn("line 3", self.context_of(out))

    # The note must tell Claude to fix the file. The note must also tell Claude
    # to ask the eight questions. The scanner cannot answer those questions.
    # So a file can be hard to read even when the scanner finds no faults.
    def test_note_says_to_fix_the_file_and_read_the_questions(self):
        path = self.prose_file("memo.md", "a %s b\n" % EM_DASH)
        _, out = self.run_posttool("Write", {"file_path": path})
        ctx = self.context_of(out).lower()
        self.assertIn("fix", ctx)
        self.assertIn("eight questions", ctx)

    # The note must have only ASCII characters. The note is about a long dash,
    # so it would be easy to copy that dash into the note by mistake.
    def test_note_is_pure_ascii(self):
        path = self.prose_file("memo.md", "a %s b\n" % EM_DASH)
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertTrue(all(ord(c) <= 126 for c in self.context_of(out)))

    # Claude can also save a file with a terminal command. In the terminal
    # command here, the > sign saves text in notes.qmd. The test does not run
    # the terminal command. The test makes the file itself. The script must
    # find the name of the file in the terminal command. The script must send
    # a note about the file.
    def test_bash_command_naming_a_fresh_prose_file_is_scanned(self):
        path = self.prose_file("notes.qmd", "a %s b\n" % EM_DASH)
        cmd = "cat > %s <<'EOF'\nwhatever\nEOF" % path
        _, out = self.run_posttool("Bash", {"command": cmd})
        self.assertIsNotNone(out)
        self.assertIn("notes.qmd", self.context_of(out))

    # This is like run_posttool above. It also tells the script which folder
    # Claude is working in. The name "cwd" is short for "current working
    # directory." A directory is a folder.
    def run_posttool_in(self, cwd, tool_name, tool_input):
        event = json.loads(posttool_event(tool_name, tool_input))
        event["cwd"] = cwd
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], json.dumps(event), self.log)
        out = buf.getvalue().strip()
        return code, (json.loads(out) if out else None)

    # Here "f=memo.md" gives memo.md a short name, f. Then "cat > $f" saves the
    # file. The script reads "f=memo.md" as the name of a file. There is no
    # file with that name. So the script has to find memo.md in another way.
    # It looks in the folder where Claude is working. It also looks in the
    # folders inside that one. It looks for any prose file that changed in the
    # last minute. The note must name memo.md. Jake asked about this case on
    # 2026-09-14.
    def test_bash_route_finds_a_fresh_prose_file_the_command_hides(self):
        path = self.prose_file("memo.md", "a %s b\n" % EM_DASH)
        _, out = self.run_posttool_in(self._tmp.name, "Bash",
                                      {"command": "f=memo.md; cat > $f"})
        self.assertIsNotNone(out)
        self.assertIn("memo.md", self.context_of(out))

    # Make a file. Then set the file's date back by 600 seconds. That is ten
    # minutes. The terminal command "ls" only lists files. The script must say
    # nothing, because the file did not change in the last minute.
    def test_bash_route_walk_ignores_old_files(self):
        path = self.prose_file("old.md", "a %s b\n" % EM_DASH)
        old = time.time() - 600
        os.utime(path, (old, old))
        _, out = self.run_posttool_in(self._tmp.name, "Bash",
                                      {"command": "ls"})
        self.assertIsNone(out)

    # A folder whose name starts with a dot is hidden. Programs keep their own
    # files there. The test puts a new file in each of two hidden folders. The
    # script must say nothing about those two files.
    def test_bash_route_walk_skips_git_and_hidden_directories(self):
        for sub in (".git", ".cache"):
            os.makedirs(os.path.join(self._tmp.name, sub))
            self.prose_file(os.path.join(sub, "x.md"), "a %s b\n" % EM_DASH)
        _, out = self.run_posttool_in(self._tmp.name, "Bash",
                                      {"command": "ls"})
        self.assertIsNone(out)

    # Here the script can find memo.md in two ways. The file's name is in the
    # terminal command. The file is also new in the folder. The note must name
    # the file only once.
    def test_bash_route_reports_a_file_once_when_both_routes_find_it(self):
        path = self.prose_file("memo.md", "a %s b\n" % EM_DASH)
        _, out = self.run_posttool_in(self._tmp.name, "Bash",
                                      {"command": "cat > %s" % path})
        self.assertEqual(self.context_of(out).count("memo.md"), 1)

    # Here the event does not say which folder Claude is working in. The
    # terminal command still holds the path of the file. The script must send
    # a note.
    def test_bash_route_without_a_cwd_still_reads_the_command(self):
        path = self.prose_file("memo.md", "a %s b\n" % EM_DASH)
        _, out = self.run_posttool("Bash", {"command": "cat > %s" % path})
        self.assertIsNotNone(out)

    # The terminal command here only reads an old file. It does not change the
    # file. The script must say nothing about the file.
    def test_bash_command_naming_a_stale_prose_file_is_ignored(self):
        path = self.prose_file("old.md", "a %s b\n" % EM_DASH)
        old = time.time() - 600
        os.utime(path, (old, old))
        _, out = self.run_posttool("Bash", {"command": "cat %s" % path})
        self.assertIsNone(out)

    # The terminal command here names a file that does not exist. The script
    # must give back zero. The script must say nothing.
    def test_bash_command_naming_a_missing_file_is_ignored(self):
        cmd = "cat %s" % os.path.join(self._tmp.name, "nowhere.tex")
        code, out = self.run_posttool("Bash", {"command": cmd})
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    # The terminal command here names no prose file. The script must say
    # nothing.
    def test_bash_command_with_no_prose_path_is_silent(self):
        code, out = self.run_posttool("Bash", {"command": "ls -la && git status"})
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    # Claude saves a file with a long dash in it. The log must get one record.
    # The record must hold the path of the file. The record's tier must be
    # "mechanical".
    def test_dirty_file_is_logged_with_its_path(self):
        path = self.prose_file("memo.md", "a %s b\n" % EM_DASH)
        self.run_posttool("Write", {"file_path": path})
        recs = self.records()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["file"], path)
        self.assertEqual(recs[0]["tier"], "mechanical")

    # This event does not say which file Claude saved. The script must give
    # back zero. The script must say nothing.
    def test_missing_tool_input_exits_zero_and_silent(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], json.dumps({"hook_event_name": "PostToolUse",
                                                     "tool_name": "Write"}), self.log)
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    # This event is broken JSON. The script must give back zero. The script
    # must say nothing.
    def test_malformed_json_exits_zero_and_silent(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], "{nope", self.log)
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    # The event says that Claude saved gone.md. There is no such file. The
    # script must give back zero. The script must say nothing.
    def test_unreadable_file_exits_zero_and_silent(self):
        path = os.path.join(self._tmp.name, "gone.md")
        code, out = self.run_posttool("Write", {"file_path": path})
        self.assertEqual(code, 0)
        self.assertIsNone(out)


# This function makes a very small Word file. A Word file is really a zip
# file with other files inside it. One of those files is word/document.xml.
# The file word/document.xml holds the words. In it, the mark <w:p> starts a
# paragraph. The mark <w:t> starts the text. "paragraphs" is a list of the
# paragraphs to put in the Word file.
def make_docx(path, paragraphs):
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


# Does the script look for faults in Word files?
#
# Jake gets Word files from people he works with. The script takes the words
# out of a Word file, one paragraph at a time. It must not look at marks such
# as <w:p>, because nobody wrote those as prose.
class TestDocx(GateCase):

    # Run the posttool command. Give back "code" and "out".
    def run_posttool(self, tool_name, tool_input):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], posttool_event(tool_name, tool_input),
                           self.log)
        out = buf.getvalue().strip()
        return code, (json.loads(out) if out else None)

    # Make a Word file with two paragraphs. The second one has a long dash.
    # The note must name the file. The note must name the kind of fault. The
    # note must not have "w:" in it, because that would mean the script had
    # read the marks.
    def test_paragraph_text_is_scanned_and_markup_is_not(self):
        path = make_docx(os.path.join(self._tmp.name, "memo.docx"),
                         ["The estimand is the average treatment effect.",
                          "The estimate %s not the estimand." % EM_DASH])
        code, out = self.run_posttool("Write", {"file_path": path})
        self.assertEqual(code, 0)
        ctx = self.context_of(out)
        self.assertIn("memo.docx", ctx)
        self.assertIn("unicode", ctx)
        self.assertNotIn("w:", ctx, "the note has marks from the Word file")

    # The long dash is in the third paragraph. A Word file has no line numbers.
    # So the note must say "paragraph 3".
    def test_note_numbers_the_paragraph(self):
        path = make_docx(os.path.join(self._tmp.name, "memo.docx"),
                         ["clean", "clean", "a %s b" % EM_DASH])
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertIn("paragraph 3", self.context_of(out))

    # The script must say nothing about a clean Word file.
    def test_a_clean_docx_is_silent(self):
        path = make_docx(os.path.join(self._tmp.name, "memo.docx"),
                         ["The estimand is the average treatment effect."])
        code, out = self.run_posttool("Write", {"file_path": path})
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    # The test makes a file named broken.docx. A real Word file is a zip file.
    # This one holds only plain text. The script must give back zero. The
    # script must say nothing.
    def test_a_docx_that_is_not_a_zip_is_silent(self):
        path = os.path.join(self._tmp.name, "broken.docx")
        with open(path, "w") as fh:
            fh.write("not a zip %s" % EM_DASH)
        code, out = self.run_posttool("Write", {"file_path": path})
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    # Here a terminal command makes the Word file. The program pandoc turns
    # one type of document into another type. The script must find the Word
    # file. The note must have the Word file's name in it.
    def test_docx_is_found_by_the_bash_route(self):
        path = make_docx(os.path.join(self._tmp.name, "memo.docx"),
                         ["a %s b" % EM_DASH])
        event = json.loads(posttool_event("Bash", {"command": "pandoc memo.md -o memo.docx"}))
        event["cwd"] = self._tmp.name
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sg.main(["posttool"], json.dumps(event), self.log)
        self.assertIn("memo.docx", buf.getvalue())

    # Word sometimes cuts a sentence into pieces, for example when one part is
    # in italics. Each piece is marked <w:r>. The test makes a Word file with
    # one sentence in two pieces. The first piece ends with "is". The second
    # piece is one word. The scanner reports `is appropriate` as a fault. It
    # can find these two words together only if the script joins the pieces.
    # The note must name that kind of fault.
    def test_extractor_joins_runs_within_a_paragraph(self):
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


# Can the script find a file when a terminal command moves to another folder?
#
# In a terminal, "cd" means "change directory." It moves you to another
# folder. After "cd papers", the name memo.md means the memo.md in the folder
# papers. Claude Code tells the script only the folder where Claude was before
# the terminal command. So the script has to read each "cd" in the terminal
# command. The script has to follow each one. Jake asked for this on
# 2026-09-14.
#
# In a terminal command, "&&" means "if that worked, do this next." The mark
# ";" means "do this next, even if that did not work."
class TestChangeDirectory(GateCase):

    # "command" is a terminal command. "cwd" is the folder where Claude was
    # before the terminal command. Run the posttool command as if Claude had
    # just run the terminal command.
    def run_bash(self, cwd, command):
        event = json.loads(posttool_event("Bash", {"command": command}))
        event["cwd"] = cwd
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], json.dumps(event), self.log)
        out = buf.getvalue().strip()
        return code, (json.loads(out) if out else None)

    # Make a file with a long dash in it, in this folder. If the folder does
    # not exist, make it first.
    def dirty(self, directory, name):
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("a %s b\n" % EM_DASH)
        return path

    # The terminal command moves to the folder "elsewhere". Then it saves
    # memo.md there. The "cd" gives the path of the folder. The script must
    # send a note about memo.md.
    def test_relative_name_after_an_absolute_cd(self):
        other = os.path.join(self._tmp.name, "elsewhere")
        self.dirty(other, "memo.md")
        _, out = self.run_bash(self._tmp.name, "cd %s && cat > memo.md" % other)
        self.assertIsNotNone(out)
        self.assertIn("memo.md", self.context_of(out))

    # Here the "cd" gives only the folder's name, "sub". The script must look
    # for "sub" inside the folder where Claude was. The script must send a
    # note.
    def test_relative_cd_is_taken_from_the_reported_cwd(self):
        self.dirty(os.path.join(self._tmp.name, "sub"), "memo.md")
        _, out = self.run_bash(self._tmp.name, "cd sub && cat > memo.md")
        self.assertIsNotNone(out)

    # Here the terminal command moves to another folder. It also gives memo.md
    # the short name f. The script must look in the other folder for prose
    # files that just changed. The script must send a note.
    def test_hidden_name_after_cd_is_found_by_the_search(self):
        other = os.path.join(self._tmp.name, "elsewhere")
        self.dirty(other, "memo.md")
        _, out = self.run_bash(self._tmp.name,
                               "cd %s && f=memo.md; cat > $f" % other)
        self.assertIsNotNone(out)

    # Here the folder's name has spaces in it. So the terminal command has
    # quotation marks around the path. The script must still send a note.
    def test_quoted_directory_with_a_space(self):
        other = os.path.join(self._tmp.name, "dir with space")
        self.dirty(other, "memo.md")
        _, out = self.run_bash(self._tmp.name,
                               'cd "%s" && cat > memo.md' % other)
        self.assertIsNotNone(out)

    # Here the terminal command moves to a folder named "a". Then it moves to a
    # folder named "b" inside the first one. The script must follow both moves.
    # The script must send a note.
    def test_two_cds_are_followed_in_order(self):
        deep = os.path.join(self._tmp.name, "a", "b")
        self.dirty(deep, "memo.md")
        _, out = self.run_bash(self._tmp.name, "cd a && cd b && cat > memo.md")
        self.assertIsNotNone(out)

    # Here the "cd" names a folder that does not exist. The script must give
    # back zero. The script must say nothing.
    def test_cd_to_a_missing_directory_is_silent(self):
        code, out = self.run_bash(self._tmp.name,
                                  "cd /no/such/dir && cat > memo.md")
        self.assertEqual(code, 0)
        self.assertIsNone(out)

    # In a terminal, "cd" with no folder after it moves to your home folder.
    # This test must not save a file in Jake's home folder. So the test checks
    # only that the script gives back zero.
    def test_cd_with_no_argument_means_home(self):
        code, _ = self.run_bash(self._tmp.name, "cd && ls")
        self.assertEqual(code, 0)


# What does the script do with a file that the scanner cannot read?
#
# The scanner cannot read .rtf files. On 2026-09-14 Jake chose not to have the
# scanner read them. He asked for a warning when Claude saves one. So the
# script sends Claude a note. The note tells Claude to warn Jake that the file
# was not checked.
class TestUncheckedFormats(GateCase):

    # Run the posttool command. "cwd" is the folder Claude is working in. A
    # test can leave it out.
    def run_posttool(self, tool_name, tool_input, cwd=None):
        event = json.loads(posttool_event(tool_name, tool_input))
        if cwd:
            event["cwd"] = cwd
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], json.dumps(event), self.log)
        out = buf.getvalue().strip()
        return code, (json.loads(out) if out else None)

    # Make an .rtf file with a long dash in it.
    def rtf(self, name="notes.rtf"):
        path = os.path.join(self._tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{\\rtf1\\ansi The estimate %s not the estimand.}" % EM_DASH)
        return path

    # Claude saves an .rtf file. The note must name the file. The note must say
    # "not checked". The note must say "tell Jake".
    def test_writing_an_rtf_file_warns_and_says_to_tell_jake(self):
        path = self.rtf()
        code, out = self.run_posttool("Write", {"file_path": path})
        self.assertEqual(code, 0)
        ctx = self.context_of(out)
        self.assertIn("notes.rtf", ctx)
        self.assertIn("not checked", ctx.lower())
        self.assertIn("tell jake", ctx.lower())

    # The note must not list the long dash as a fault, because the scanner
    # did not read the file.
    def test_rtf_content_is_not_scanned(self):
        path = self.rtf()
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertNotIn("unicode", self.context_of(out))

    # Here a terminal command saves the .rtf file. The note must name the file.
    def test_rtf_named_in_a_bash_command_warns(self):
        path = self.rtf()
        _, out = self.run_posttool("Bash", {"command": "pandoc memo.md -o %s" % path})
        self.assertIn("notes.rtf", self.context_of(out))

    # Here the terminal command gives the .rtf file the short name f. The
    # script must find the new file in the folder. The script must send a note.
    def test_fresh_rtf_found_by_the_search_warns(self):
        self.rtf()
        _, out = self.run_posttool("Bash", {"command": "f=notes.rtf; cat > $f"},
                                   cwd=self._tmp.name)
        self.assertIsNotNone(out)

    # The log must get one record. The record's tier must be "unchecked". That
    # means the scanner did not read the file. The record must also hold the
    # path of the file.
    def test_rtf_warning_is_logged_as_unchecked(self):
        path = self.rtf()
        self.run_posttool("Write", {"file_path": path})
        recs = self.records()
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["tier"], "unchecked")
        self.assertEqual(recs[0]["file"], path)

    # The note must have only ASCII characters.
    def test_the_warning_is_pure_ascii(self):
        path = self.rtf()
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertTrue(all(ord(c) <= 126 for c in self.context_of(out)))


# Which faults are the mechanical ones?
class TestTierMembershipIsOneLine(unittest.TestCase):

    # The script keeps the names of the mechanical kinds of faults in one list.
    # The list is named MECHANICAL. It must hold "unicode",
    # "bold-run-in-opener", and "dash-semicolon". It must hold no other names.
    def test_mechanical_categories_declared_in_one_place(self):
        self.assertEqual(set(sg.MECHANICAL),
                         {"unicode", "bold-run-in-opener", "dash-semicolon"})


# What does the script do with an attention fault?
#
# The scanner reports a trailing-clause on about one line in fourteen. Many of
# those lines are fine. If a note listed all of them, Claude might miss the
# mechanical faults. So the script leaves attention faults out of its notes
# about files. The stop command still lists attention faults in the log.
class AttentionCategoryTests(GateCase):

    # Make a list of two faults. The first is a trailing-clause. The second is
    # a long dash. Ask the script to write the note about them. The note must
    # name the long dash's kind of fault, "unicode". It must not name
    # trailing-clause.
    def test_trailing_clause_is_not_named_in_the_note(self):
        findings = [("memo.md", 1, "trailing-clause", ", which is what"),
                    ("memo.md", 2, "unicode", "\u2014")]
        note = sg.build_file_note("memo.md", findings)
        self.assertNotIn("trailing-clause", note)
        self.assertIn("unicode", note)

    # Here the only fault is a trailing-clause. The script must write no note
    # at all.
    def test_a_file_with_only_attention_categories_gets_no_note_at_all(self):
        self.assertIsNone(sg.build_file_note(
            "memo.md", [("memo.md", 1, "trailing-clause", ", and the")]))

    # Run the stop command on a reply that has a trailing-clause. The record
    # in the log must list it.
    def test_the_category_is_still_logged(self):
        self.run_stop("We drew the sample, which is what the design asks for.")
        self.assertIn("trailing-clause", self.records()[0]["categories"])


# Does the script say the same thing twice?
#
# It used to do that. From 2026-09-14 to 2026-09-20 the script sent 2156 notes
# about files. Of those notes, 1675 were exactly the same as the last note
# about the same file. A repeated note tells Claude nothing new. So now the
# script remembers what it has said about each file in each session. It sends
# only what is new.
class TestFileNoteRepeats(GateCase):

    # Make a file with this name and this text.
    def prose_file(self, name, text):
        path = os.path.join(self._tmp.name, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    # Run the posttool command. A test can choose the name of the session.
    def run_posttool(self, tool_name, tool_input, session="s1"):
        event = json.loads(posttool_event(tool_name, tool_input))
        event["session_id"] = session
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.main(["posttool"], json.dumps(event), self.log)
        out = buf.getvalue().strip()
        return code, (json.loads(out) if out else None)

    # Claude saves a file with a fault. The script must send a note. Then
    # Claude saves the file again with the same fault. The script must say
    # nothing the second time.
    def test_second_scan_with_the_same_findings_is_silent(self):
        path = self.prose_file("memo.md", "The estimand %s the estimate.\n" % EM_DASH)
        _, first = self.run_posttool("Write", {"file_path": path})
        self.assertIsNotNone(first)
        code, second = self.run_posttool("Edit", {"file_path": path})
        self.assertEqual(code, 0)
        self.assertIsNone(second)

    # Claude saves a file with a long dash. Then Claude adds a sentence with a
    # new fault, the words `is appropriate`. The second note must list the new
    # fault. The second note must not list the long dash again. In a note, the
    # script writes the long dash as U+2014.
    def test_only_the_new_finding_is_reported_on_a_rescan(self):
        path = self.prose_file("memo.md", "The estimand %s the estimate.\n" % EM_DASH)
        self.run_posttool("Write", {"file_path": path})
        with open(path, "a", encoding="utf-8") as fh:
            fh.write("\nThe design is appropriate here.\n")
        _, out = self.run_posttool("Edit", {"file_path": path})
        ctx = self.context_of(out)
        self.assertIn("appropriate", ctx)
        self.assertNotIn("U+2014", ctx)

    # Claude saves a file with a long dash. Then Claude adds a line at the top
    # of the file. Now the long dash is on a later line. It is still the same
    # fault. The script must say nothing the second time.
    def test_a_finding_that_moved_lines_is_not_new(self):
        path = self.prose_file("memo.md", "The estimand %s the estimate.\n" % EM_DASH)
        self.run_posttool("Write", {"file_path": path})
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("A new clean first line.\n\nThe estimand %s the estimate.\n" % EM_DASH)
        _, out = self.run_posttool("Edit", {"file_path": path})
        self.assertIsNone(out)

    # Claude saves a file with a long dash. Then Claude takes the long dash out
    # of the file. The script must say nothing the second time.
    def test_a_fixed_finding_produces_no_note(self):
        path = self.prose_file("memo.md", "The estimand %s the estimate.\n" % EM_DASH)
        self.run_posttool("Write", {"file_path": path})
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("The estimand --- the estimate.\n")
        _, out = self.run_posttool("Edit", {"file_path": path})
        self.assertIsNone(out)

    # Claude saves a file in session s1. The script sends a note there. Then
    # Claude saves the same file in session s2. The script has not sent a note
    # in session s2. So the script must send the note there too.
    def test_another_session_gets_the_full_note(self):
        path = self.prose_file("memo.md", "The estimand %s the estimate.\n" % EM_DASH)
        self.run_posttool("Write", {"file_path": path}, session="s1")
        _, out = self.run_posttool("Write", {"file_path": path}, session="s2")
        self.assertIn("U+2014", self.context_of(out))

    # Claude saves the same file twice with the same fault. The log must have
    # only one record, because the script sent only one note.
    def test_a_repeat_is_not_logged_as_a_dirty_file(self):
        path = self.prose_file("memo.md", "The estimand %s the estimate.\n" % EM_DASH)
        self.run_posttool("Write", {"file_path": path})
        self.run_posttool("Edit", {"file_path": path})
        self.assertEqual(len(self.records()), 1)

    # The script keeps what it remembers in a file. Here the test puts a
    # folder where that file should be. So the script cannot remember
    # anything. It must send the full note both times. A repeated note is
    # better than a missing one.
    def test_unwritable_state_still_reports_the_full_note(self):
        path = self.prose_file("memo.md", "The estimand %s the estimate.\n" % EM_DASH)
        state = sg.state_path(self.log)
        os.makedirs(os.path.dirname(state), exist_ok=True)
        os.makedirs(state)
        _, out = self.run_posttool("Write", {"file_path": path})
        self.assertIn("U+2014", self.context_of(out))
        _, again = self.run_posttool("Edit", {"file_path": path})
        self.assertIn("U+2014", self.context_of(again))


# This function makes a fake transcript. Each line of a transcript holds one
# message in the session.
#
# "turns" is a list. Each item has a kind and some text. The kind is "user"
# for something Jake typed. It is "assistant" for something Claude wrote. It
# is "tool_result" for what a tool gave back to Claude. Jake does not see
# tool results.
#
# Each line of the kind "assistant" also has the word "private" in it. That
# word stands for Claude's thinking. Jake does not see Claude's thinking.
def transcript_file(directory, turns):
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


# Does the check command work?
#
# Claude runs the check command on a draft before it sends the draft. First
# the scanner looks for faults. Then the reader reads the draft one sentence
# at a time. The command prints what both of them found.
#
# Why have a reader? Claude once wrote "registry count" to Jake. Claude had
# read a file that Jake had not seen. So Claude knew what the words meant, but
# Jake did not. A writer cannot see this kind of mistake. Someone else can, if
# that person has seen only what Jake has seen. Jake asked for such a reader
# on 2026-09-20.
#
# The real reader needs the internet. These tests use fake readers, so that
# the tests can run without it.
class TestCheck(GateCase):

    # Before each test, do what GateCase does. Then make an empty list. The
    # fake reader will use the list to keep what the script sends to it.
    def setUp(self):
        super().setUp()
        self.calls = []

    # This is the fake reader. The script sends it a request. A request to an
    # AI model is called a prompt. The fake reader keeps the prompt. Then it
    # gives back one complaint: the words "Two gaps." have no main verb.
    def fake_reader(self, prompt):
        self.calls.append(prompt)
        return json.dumps([{"sentence": "Two gaps.", "meaning": "CANNOT",
                            "verdict": "stop", "words": "Two gaps.",
                            "why": "No main verb."}])

    # Make a file that holds the draft.
    def draft(self, text):
        path = os.path.join(self._tmp.name, "draft.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    # Run the check command on a draft. Use the fake reader unless the test
    # gives another one. Give back "code" and "out".
    def run_check(self, draft_path, transcript=None, reader=None):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = sg.run_check(draft_path, self.log, transcript,
                                reader or self.fake_reader)
        return code, buf.getvalue()

    # The draft has a long dash in it. The command must print U+2014. That is
    # how the script writes the long dash in ASCII.
    def test_scanner_findings_are_printed(self):
        path = self.draft("The estimand %s the estimate.\n" % EM_DASH)
        code, out = self.run_check(path)
        self.assertEqual(code, 0)
        self.assertIn("U+2014", out)

    # The fake reader complains about "Two gaps." The command must print those
    # words. It must also print the reason that the reader gave.
    def test_reader_findings_are_printed_with_the_offending_words(self):
        path = self.draft("Two gaps. A path is invisible.\n")
        _, out = self.run_check(path)
        self.assertIn("Two gaps.", out)
        self.assertIn("No main verb.", out)

    # The script must send the draft to the reader once. The test looks for a
    # sentence of the draft in what the reader got.
    def test_reader_receives_the_draft(self):
        path = self.draft("Two gaps. A path is invisible.\n")
        self.run_check(path)
        self.assertEqual(len(self.calls), 1)
        self.assertIn("A path is invisible.", self.calls[0])

    # Make a transcript with a question from Jake, an answer from Claude, and
    # a tool result. The reader must get the question and the answer, because
    # Jake saw them. The reader must not get the tool result or Claude's
    # thinking, because Jake did not see them.
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

    # The script sends the reader Jake's last four messages. It also sends
    # everything Claude wrote after the first of those four. Here Jake asks one
    # question. Then Claude writes twelve short messages. The reader must still
    # get Jake's question. An older version of the script counted Claude's
    # messages along with Jake's, so it left out Jake's question.
    def test_jakes_turns_survive_a_run_of_assistant_status_lines(self):
        turns = [("user", "What is the registry count?")]
        turns += [("assistant", "Still working, status %d." % i) for i in range(12)]
        transcript = transcript_file(self._tmp.name, turns)
        path = self.draft("Twenty.\n")
        self.run_check(path, transcript=transcript)
        self.assertIn("What is the registry count?", self.calls[0])

    # Jake said on 2026-09-20 what the reader should do. The reader should ask
    # what each sentence means. The reader should also put other nouns in the
    # sentence. If the verb fits any noun, then the verb says little. The test
    # looks for three things in the prompt: the words "sentence by sentence",
    # the words "what does this sentence mean", and the word "nouns".
    def test_reader_is_asked_what_each_sentence_means(self):
        path = self.draft("A sentence.\n")
        self.run_check(path)
        prompt = self.calls[0].lower()
        self.assertIn("sentence by sentence", prompt)
        self.assertIn("what does this sentence mean", prompt)
        self.assertIn("nouns", prompt)

    # The script must not send the reader a list of words to look for. With a
    # list, the reader would look only for those words. The scanner already
    # looks for them. The test checks that three such words are not in the
    # prompt.
    def test_reader_prompt_names_no_banned_words(self):
        path = self.draft("A sentence.\n")
        self.run_check(path)
        for word in ("load-bearing", "appropriate", "costs"):
            self.assertNotIn(word, self.calls[0])

    # This fake reader always fails, as if the internet were down. The command
    # must give back zero. It must still print what the scanner found. It must
    # say that the reader did not run.
    def test_reader_failure_leaves_the_scanner_findings_and_says_so(self):
        def broken(prompt):
            raise OSError("no network")
        path = self.draft("The estimand %s the estimate.\n" % EM_DASH)
        code, out = self.run_check(path, reader=broken)
        self.assertEqual(code, 0)
        self.assertIn("U+2014", out)
        self.assertIn("reader did not run", out.lower())

    # The reader is supposed to answer in JSON. This fake reader answers with a
    # plain sentence. The script cannot use that. The script must say that the
    # reader did not run.
    #
    # "lambda p: ..." is a short way to write a function in Python. This one
    # gives back the same sentence no matter what it is sent.
    def test_reader_returning_prose_instead_of_json_is_reported_as_not_run(self):
        path = self.draft("A sentence.\n")
        code, out = self.run_check(path, reader=lambda p: "Ready for the next question.")
        self.assertEqual(code, 0)
        self.assertIn("reader did not run", out.lower())

    # This draft is clean. This fake reader gives back "[]". That is an empty
    # list, because the reader has no complaints. The check command must print
    # the word "nothing", as in "Nothing found".
    def test_a_clean_draft_says_so_in_one_line(self):
        path = self.draft("The estimand differs from the estimate.\n")
        _, out = self.run_check(path, reader=lambda p: "[]")
        self.assertIn("nothing", out.lower())

    # Run the check command on a draft. Then run the stop command on a reply
    # with the same words. The last record in the log must say that the reply
    # was checked.
    def test_check_records_the_draft_for_the_stop_hook(self):
        path = self.draft("The estimand differs from the estimate.\n")
        self.run_check(path, reader=lambda p: "[]")
        _, _ = self.run_stop("The estimand differs from the estimate.")
        rec = self.records()[-1]
        self.assertTrue(rec["checked"])


# Does the reader know what the project is for?
#
# A project can have a file named POINT.md. The file says who reads the work.
# It says what the work should do for them. Jake has agreed to what it says.
# The script sends this file to the reader. Then the reader can ask whether a
# paragraph helps the project.
#
# To find POINT.md, the script looks in the folder where Claude is working. If
# the file is not there, the script looks in the folder above. It keeps going
# up until it reaches the project's top folder. The top folder is the one that
# holds a folder named .git.
class TestPointOfTheProject(GateCase):

    # Before each test, make a fake project in a folder named proj. Put a .git
    # folder in proj. Put a folder named Paper in proj too. Put a folder named
    # sections in Paper.
    def setUp(self):
        super().setUp()
        self.calls = []
        self.proj = os.path.join(self._tmp.name, "proj")
        self.deep = os.path.join(self.proj, "Paper", "sections")
        os.makedirs(self.deep)
        os.makedirs(os.path.join(self.proj, ".git"))

    # This fake reader keeps what it was sent. It has no complaints.
    def capture(self, prompt):
        self.calls.append(prompt)
        return "[]"

    # Save this text in a file. Give back the path of the file.
    def write(self, path, text):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    # Make a file that holds a draft.
    def draft(self, text="The estimand differs from the estimate.\n"):
        return self.write(os.path.join(self._tmp.name, "draft.md"), text)

    # Run the check command. "point_path" is the path of a POINT.md, or None.
    # Give back the prompt that the reader got.
    def check(self, point_path):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sg.run_check(self.draft(), self.log, None, self.capture,
                         point_path=point_path)
        return self.calls[-1]

    # Put POINT.md in the project's top folder. Start looking from the folder
    # "sections", two folders down. The script must find the file.
    def test_point_file_is_found_from_a_subdirectory_of_the_project(self):
        point = self.write(os.path.join(self.proj, "POINT.md"), "x\n")
        self.assertEqual(sg.find_point_file(self.deep), point)

    # Put POINT.md in the folder above the project. That file belongs to
    # something else. The script must not use it.
    def test_walk_stops_at_the_project_root(self):
        self.write(os.path.join(self._tmp.name, "POINT.md"), "x\n")
        self.assertIsNone(sg.find_point_file(self.deep))

    # There is no POINT.md anywhere. The script must give back None.
    def test_no_point_file_gives_none(self):
        self.assertIsNone(sg.find_point_file(self.deep))

    # Put some words in POINT.md. The reader must get those words.
    def test_point_text_reaches_the_reader(self):
        point = self.write(os.path.join(self.proj, "POINT.md"),
                           "Readers: methodologists choosing a test.\n")
        prompt = self.check(point)
        self.assertIn("Readers: methodologists choosing a test.", prompt)

    # There is no POINT.md. The script must tell the reader so. Otherwise the
    # reader might make up a purpose for the project.
    def test_without_a_point_the_reader_is_told_none_is_on_file(self):
        prompt = self.check(None)
        self.assertIn("no statement of the point", prompt.lower())

    # This POINT.md has ten thousand words. The script sends POINT.md and the
    # conversation to the reader together. The reader should not get a very
    # long POINT.md. So the script must cut it. The number POINT_CHARS in the
    # script says how many characters the script may keep.
    def test_a_long_point_file_is_cut(self):
        point = self.write(os.path.join(self.proj, "POINT.md"),
                           "word " * 10000)
        self.assertLessEqual(len(sg.read_point(point)), sg.POINT_CHARS)

    # Claude can tell the check command which transcript and which POINT.md to
    # use. Claude does this with the words "--transcript" and "--point". The
    # test gives the script the names of a draft, a transcript, and a
    # POINT.md. The script must pick out all three names. Then the test gives
    # the script only the name of a draft. The script must pick out that name.
    # The script must give back None for the other two.
    def test_check_takes_the_point_and_transcript_from_flags(self):
        draft, transcript, point = sg.parse_check_args(
            ["check", "d.md", "--transcript", "t.jsonl", "--point", "p.md"])
        self.assertEqual((draft, transcript, point),
                         ("d.md", "t.jsonl", "p.md"))
        self.assertEqual(sg.parse_check_args(["check", "d.md"]),
                         ("d.md", None, None))

    # The check command must say which POINT.md the reader got. If the reader
    # got none, the command must say so. Then the command must also say in
    # which folder it started to look. That lets Claude see whether it was the
    # wrong folder.
    # The test runs the command once with a POINT.md and once without one.
    # os.getcwd() is the folder where Python is working.
    def test_check_says_which_point_file_the_reader_got(self):
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

    # The second of the eight questions must ask two things. What question
    # does the passage answer? What does the answer do for the point of the
    # project? Python starts counting at 0, so QUESTIONS[1] is the second one.
    def test_question_2_asks_what_the_passage_does_for_the_point(self):
        q = sg.QUESTIONS[1].lower()
        self.assertIn("what question it answers", q)
        self.assertIn("point", q)


# Can the check command find the transcript by itself?
#
# Claude Code keeps the transcripts in Jake's home folder, inside
# .claude/projects. Suppose a session is in /Users/j/repos/ai_workflow. Claude
# Code keeps the transcript of that session in a folder named
# -Users-j-repos-ai-workflow. To make that name, Claude Code takes the path.
# Then it changes each character that is not a letter or a number into a
# hyphen.
class TestNewestTranscript(unittest.TestCase):

    # Make a fake home folder with two transcripts. Set the date of the first
    # one to long ago. The script must choose the newer one. The path in this
    # test has an underscore in it. An older version of the script did not
    # change the underscore to a hyphen, so it found nothing.
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

    # Jake can have two sessions open in the same folder. Each session has a
    # name of its own. The transcript of session abc is the file abc.jsonl.
    # Here the other session's file is newer. When the script is given the
    # name abc, it must choose abc.jsonl. When it is given no name, it must
    # choose the newer file.
    def test_session_id_wins_over_the_newer_file(self):
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

    # There is no transcript. The script must give back None.
    def test_no_transcript_gives_none(self):
        with tempfile.TemporaryDirectory() as home:
            self.assertIsNone(sg.newest_transcript("/nowhere/at/all", home))


# Does the script ignore the reader's own messages?
#
# To start the reader, the script starts Claude Code a second time. So Claude
# Code runs the same hooks for the reader. On 2026-09-20 the stop command wrote
# 40 records about things the reader said. Those records do not belong in
# Jake's log.
#
# Now the script sets a mark when it starts the reader. A mark is a named value
# that one program hands to the programs it starts. This mark is named
# STYLE_GATE_READER. Each hook must do nothing when it finds the mark.
class TestHooksStaySilentInsideTheReader(GateCase):

    # Before each test, set the mark.
    def setUp(self):
        super().setUp()
        os.environ[sg.READER_MARK] = "1"

    # After each test, take the mark away.
    def tearDown(self):
        os.environ.pop(sg.READER_MARK, None)
        super().tearDown()

    # Run the stop command on a reply with a fault while the mark is set. The
    # command must give back zero. The command must print nothing. The command
    # must add nothing to the log.
    def test_stop_writes_nothing_inside_the_reader(self):
        code, out = self.run_stop("a %s b" % EM_DASH)
        self.assertEqual(code, 0)
        self.assertIsNone(out)
        self.assertEqual(self.records(), [])

    # Run the preflight command while the mark is set. The command must print
    # nothing.
    def test_preflight_injects_nothing_inside_the_reader(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sg.main(["preflight"], "", self.log)
        self.assertEqual(buf.getvalue().strip(), "")

    # This test checks only that the mark has the right name. It does not
    # start the real reader, because the real reader needs the internet.
    def test_the_reader_process_gets_the_mark(self):
        self.assertEqual(sg.READER_MARK, "STYLE_GATE_READER")


# Does the script wait for input only when some is coming?
#
# One program can send text to a second program while the second one is
# running. The second program reads the text from a place called stdin. The
# name is short for "standard input." Claude Code sends events to the hooks
# through stdin. Nobody sends anything to the check command that way. On
# 2026-09-20 the check command waited for text that never came. So the command
# never finished.
class TestStdinIsReadOnlyByHooks(unittest.TestCase):

    # The stop and posttool commands must read stdin, because their events
    # come in there.
    def test_hook_entry_points_read_stdin(self):
        self.assertTrue(sg.reads_stdin(["stop"]))
        self.assertTrue(sg.reads_stdin(["posttool"]))

    # The check command must not read stdin. The preflight command must not
    # read stdin either. It is a hook, but it prints the same reminder each
    # time. So it does not need its event. If someone runs the script without
    # naming a command, the script must not read stdin.
    def test_check_and_preflight_do_not(self):
        self.assertFalse(sg.reads_stdin(["check", "draft.md"]))
        self.assertFalse(sg.reads_stdin(["preflight"]))
        self.assertFalse(sg.reads_stdin([]))

    # This test runs the real script as a separate program. The test opens the
    # program's stdin. It sends nothing. It does not close stdin until the
    # program has finished. The program must finish within 20 seconds. If the
    # program does not finish, the test stops the program and fails.
    #
    # The test also makes sure that the reader cannot start. PATH=d tells the
    # computer to look for programs only in the test folder, d. The only file
    # there is the draft. So the check command must print "Reader did not run".
    #
    # CLAUDECODE="1" tells the script that it is running in Claude Code. In any
    # other program the script does not try to start the reader.
    def test_check_returns_when_stdin_never_closes(self):
        script = os.path.abspath(sg.__file__)
        with tempfile.TemporaryDirectory() as d:
            draft = os.path.join(d, "draft.md")
            with open(draft, "w") as fh:
                fh.write("A sentence.\n")
            env = dict(os.environ, PATH=d, CLAUDECODE="1")
            import subprocess
            proc = subprocess.Popen(
                [sys.executable, script, "check", draft, "--transcript",
                 os.path.join(d, "none.jsonl")],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, env=env)
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                self.fail("the check command waited for input")
            out, _ = proc.communicate()
            self.assertIn("Reader did not run", out)


# Does the log say whether a reply was checked before it was sent?
#
# On 2026-09-20 Jake said that he did not want to keep asking Claude whether
# it had checked a reply. So each record about a reply has a part named
# "checked". That part is true when Claude ran the check command on a draft
# of the reply less than two hours before it sent the reply.
#
# Claude may change a few words after the check. So the script compares the
# sentences in the reply with the sentences in the draft. The reply counts as
# checked when at least 6 in 10 of its sentences were in the draft.
class TestStopRecordsWhetherTheReplyWasChecked(GateCase):

    # Run the check command on this text, with a fake reader that has no
    # complaints. Throw away what the command prints.
    def check_draft(self, text):
        path = os.path.join(self._tmp.name, "draft.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sg.run_check(path, self.log, None, lambda p: "[]")

    # Claude did not run the check command on this reply. The record must say
    # so.
    def test_unchecked_reply_is_recorded_as_unchecked(self):
        self.run_stop("Nobody checked this clean reply.")
        recs = self.records()
        self.assertEqual(len(recs), 1)
        self.assertFalse(recs[0]["checked"])

    # This reply has the same words as a draft that was checked. The record
    # must say that the reply was checked.
    def test_checked_reply_is_recorded_as_checked(self):
        self.check_draft("The estimand differs from the estimate. The estimator differs from both.\n")
        self.run_stop("The estimand differs from the estimate. The estimator differs from both.")
        self.assertTrue(self.records()[-1]["checked"])

    # The draft had five sentences. In the reply, the first four are the same.
    # The fifth is new. So 4 in 5 of the sentences were checked. The record
    # must say that the reply was checked.
    def test_a_lightly_edited_reply_still_counts_as_checked(self):
        self.check_draft("This is one. This is two. This is three. This is four. This is five.\n")
        self.run_stop("This is one. This is two. This is three. This is four. The fifth one is new.")
        self.assertTrue(self.records()[-1]["checked"])

    # No sentence in this reply was in the draft. The record must say that the
    # reply was not checked.
    def test_an_all_new_reply_does_not_count_as_checked(self):
        self.check_draft("This is one. This is two.\n")
        self.run_stop("This reply is new. It has four sentences. The draft had two others. None of them match.")
        self.assertFalse(self.records()[-1]["checked"])

    # Claude did not run the check command on this clean reply. The stop
    # command must still print nothing.
    def test_a_clean_unchecked_reply_gets_no_note(self):
        _, out = self.run_stop("Nobody checked this clean reply.")
        self.assertIsNone(out)

    # The record of a clean reply must have the tier "clean".
    def test_clean_reply_record_carries_a_clean_tier(self):
        self.run_stop("This reply is clean.")
        self.assertEqual(self.records()[0]["tier"], "clean")


# Does the script ask Claude to audit a document before Claude replies?
#
# The style-audit skill tells Claude how to read a whole document and look for
# faults. Using that skill on a document is called an audit. Claude should
# audit each document that Claude saves. Another script, audit_guard.py, runs
# after Claude has replied. If Claude skipped an audit, that script tells
# Claude to do the audit and then send the reply again. It is better to ask
# for the audit earlier. So the posttool command asks for the audit the first
# time that Claude saves the document in a session. Jake chose this on
# 2026-10-26.
#
# A prose file in either of two places does not count as a document. The first
# place is the scratch folder. That is a folder for temporary files. Claude
# keeps drafts of replies there. The second place is the folder named .claude
# in Jake's home folder. Claude Code keeps its settings there. Claude also keeps
# files there of things it wants to remember.
class TestAuditBeforeAnswering(GateCase):

    # Before each test, make three folders: a fake home folder, a fake
    # project, and a fake scratch folder.
    def setUp(self):
        super().setUp()
        self.home = os.path.join(self._tmp.name, "home")
        self.proj = os.path.join(self._tmp.name, "proj")
        self.scratch = os.path.join(self._tmp.name, "scratch")
        for d in (self.home, self.proj, self.scratch):
            os.makedirs(d)

    # Save this text in a file in this folder. Give back the file's path.
    def save(self, folder, name, text):
        path = os.path.join(folder, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    # Run the posttool command as if Claude had just saved this file. Check
    # that it gives back zero. Give back the words of the note. If there is no
    # note, give back None.
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

    # Does this note ask for the audit? It does if it has the words
    # "style-audit" and the words "before you write to Jake".
    def asks_for_the_audit(self, note):
        text = (note or "").lower()
        return "style-audit" in text and "before you write to jake" in text

    # Claude saves a clean document. The note must ask for the audit. The note
    # must name the document. A clean document can still be hard to read. The
    # scanner cannot tell, because it cannot answer the eight questions.
    def test_a_clean_document_is_asked_for_the_audit(self):
        memo = self.save(self.proj, "memo.md", "The estimand is the average.\n")
        note = self.run_posttool(memo)
        self.assertTrue(self.asks_for_the_audit(note))
        self.assertIn("memo.md", note)

    # Claude saves a document with a fault. The note must list the fault. The
    # note must also ask for the audit.
    def test_a_dirty_document_is_asked_for_the_audit_after_its_findings(self):
        memo = self.save(self.proj, "memo.md", "a %s b\n" % EM_DASH)
        note = self.run_posttool(memo)
        self.assertIn("unicode", note)
        self.assertTrue(self.asks_for_the_audit(note))

    # Claude saves the same document three times. The test looks at the note
    # after the second save and after the third. At the second save nothing
    # has changed, so there must be no note. Before the third save Claude adds
    # a new fault. The note after the third save must list the new fault. It
    # must not ask for the audit again. During an audit Claude fixes the
    # document and saves it. If each save led to a new request, the audit would
    # never end.
    def test_the_audit_is_asked_for_once_per_document_and_session(self):
        memo = self.save(self.proj, "memo.md", "a %s b\n" % EM_DASH)
        self.run_posttool(memo)
        self.assertIsNone(self.run_posttool(memo))
        with open(memo, "a", encoding="utf-8") as fh:
            fh.write("\nThe design is appropriate here.\n")
        later = self.run_posttool(memo)
        self.assertIn("appropriate", later)
        self.assertFalse(self.asks_for_the_audit(later))

    # One folder can have two names. A link is a second name for a folder. In
    # this repository, "skills" is a link to the folder
    # plugins/ai-workflow/skills. So each file in that folder has two paths.
    # The test makes a folder and a link like these. It saves a file there. It
    # tells the script about the file by its first path. The note must ask for
    # the audit. Then the test tells the script about the same file by its
    # second path. There must be no note.
    def test_a_document_reached_through_a_link_is_asked_once(self):
        real = os.path.join(self.proj, "plugins", "skills")
        os.makedirs(real)
        os.symlink(real, os.path.join(self.proj, "skills"))
        self.save(real, "SKILL.md", "This skill is clean.\n")
        self.assertTrue(self.asks_for_the_audit(
            self.run_posttool(os.path.join(real, "SKILL.md"))))
        self.assertIsNone(self.run_posttool(
            os.path.join(self.proj, "skills", "SKILL.md")))

    # Claude saves a document in session s1. Then Claude saves the same document
    # in session s2. The script must ask for the audit in session s2 too.
    def test_another_session_is_asked_again(self):
        memo = self.save(self.proj, "memo.md", "The estimand is the average.\n")
        self.run_posttool(memo, session="s1")
        self.assertTrue(self.asks_for_the_audit(
            self.run_posttool(memo, session="s2")))

    # Claude saves two drafts of replies in the scratch folder. The first is
    # clean. The script must say nothing about it. The second has a fault. The
    # note must list the fault. The note must not ask for the audit.
    def test_a_reply_draft_in_the_scratch_area_is_not_asked(self):
        clean = self.save(self.scratch, "reply.md", "This draft is clean.\n")
        self.assertIsNone(self.run_posttool(clean))
        dirty = self.save(self.scratch, "reply2.md", "a %s b\n" % EM_DASH)
        note = self.run_posttool(dirty)
        self.assertIn("unicode", note)
        self.assertFalse(self.asks_for_the_audit(note))

    # Claude saves a clean file in the .claude folder of the fake home folder.
    # The script must say nothing.
    def test_a_file_under_dot_claude_is_not_asked(self):
        mem = self.save(os.path.join(self.home, ".claude", "memory"),
                        "fact.md", "This memory is clean.\n")
        self.assertIsNone(self.run_posttool(mem))

    # style_gate.py and audit_guard.py must agree about which files are
    # documents. If they did not, audit_guard.py could ask for an audit that
    # style_gate.py never asked for. The test gives both scripts the same four
    # paths. They are the paths of a memo in the project, a draft in the scratch
    # folder, a file in the .claude folder, and a Python file. Both scripts must
    # give the same answer for each path.
    def test_the_gate_and_the_guard_agree_on_what_a_document_is(self):
        import audit_guard as ag
        paths = [os.path.join(self.proj, "memo.md"),
                 os.path.join(self.scratch, "reply.md"),
                 os.path.join(self.home, ".claude", "memory", "fact.md"),
                 os.path.join(self.proj, "gate.py")]
        for p in paths:
            self.assertEqual(
                sg.is_document(p, self.home, (self.scratch,)),
                ag.is_document(p, self.home, (self.scratch,)), p)

    # The request for the audit must have only ASCII characters.
    def test_the_request_is_plain_ascii(self):
        memo = self.save(self.proj, "memo.md", "The estimand is the average.\n")
        self.assertTrue(all(ord(c) <= 126 for c in self.run_posttool(memo)))


# These two lines run all of the tests when someone runs this file.
if __name__ == "__main__":
    unittest.main(verbosity=2)
