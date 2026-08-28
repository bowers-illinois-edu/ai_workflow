#!/usr/bin/env python3
"""Unit tests for mine_transcripts.py, the corpus builder behind first-reader.

The substantive point of this script (METHOD.md step 1) is to recover
evidence about how one person reacts to prose. Two design facts follow, and
the tests exist to protect them:

  * The corpus must contain ONLY what the person typed. A tool result, a
    slash-command echo, a notification from another agent, or a system
    reminder is not evidence about anyone's reading. Including such a record
    would put words in the person's mouth, and the persona built downstream
    would then be a model of the harness rather than a model of the reader.

  * Each turn must be paired with the prose that provoked it. A complaint on
    its own says what the reader objected to; it does not say what the
    offending prose looked like. The (prose, reaction) pair is the unit of
    evidence, so the pairing logic is tested as carefully as the filtering.

One subtlety has its own test. The script keeps the TAIL of the preceding
assistant message, not the head, because a reader who stops partway through
a reply stopped somewhere in what they had just read, and the end of the
message is the part nearest the reaction.

Run: python3 test_mine_transcripts.py   (or via the repo-root Makefile: make test)
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
import mine_transcripts as mt  # noqa: E402


def human(text, ts="2026-08-01T10:00:00.000Z", **extra):
    """A record of the shape the harness writes when a person types a turn."""
    rec = {"type": "user", "timestamp": ts, "origin": {"kind": "human"},
           "promptSource": "sdk", "message": {"role": "user", "content": text}}
    rec.update(extra)
    return rec


def assistant(text, ts="2026-08-01T09:59:00.000Z"):
    return {"type": "assistant", "timestamp": ts,
            "message": {"role": "assistant",
                        "content": [{"type": "text", "text": text}]}}


def write_session(dirpath, project, session, records):
    """Write records as one JSONL session file under <dirpath>/<project>/."""
    proj = os.path.join(dirpath, project)
    os.makedirs(proj, exist_ok=True)
    path = os.path.join(proj, session + ".jsonl")
    with open(path, "w") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    return path


class TestTextExtraction(unittest.TestCase):
    """The harness stores message content two ways; both must be read."""

    def test_string_content(self):
        self.assertEqual(mt.text_of({"content": "hello"}), "hello")

    def test_list_of_text_blocks(self):
        msg = {"content": [{"type": "text", "text": "a"},
                           {"type": "text", "text": "b"}]}
        self.assertEqual(mt.text_of(msg), "a\nb")

    def test_tool_result_blocks_yield_nothing(self):
        """A tool result is not prose the person wrote or read as prose."""
        msg = {"content": [{"type": "tool_result", "content": "42"}]}
        self.assertEqual(mt.text_of(msg), "")

    def test_mixed_blocks_keep_only_text(self):
        msg = {"content": [{"type": "tool_use", "name": "Bash"},
                           {"type": "text", "text": "kept"}]}
        self.assertEqual(mt.text_of(msg), "kept")

    def test_missing_content(self):
        self.assertEqual(mt.text_of({}), "")


class TestKeepOnlyWhatThePersonTyped(unittest.TestCase):
    """Everything the harness generates on the person's behalf is excluded."""

    def keep(self, rec):
        return mt.is_human_turn(rec)

    def test_human_turn_kept(self):
        self.assertTrue(self.keep(human("what does 'the family' mean?")))

    def test_meta_record_dropped(self):
        self.assertFalse(self.keep(human("x", isMeta=True)))

    def test_task_notification_dropped(self):
        rec = human("agent finished")
        rec["origin"] = {"kind": "task-notification"}
        self.assertFalse(self.keep(rec))

    def test_teammate_message_dropped(self):
        """Another agent's message has no human origin and no promptSource."""
        rec = {"type": "user", "timestamp": "2026-08-01T10:00:00.000Z",
               "message": {"role": "user",
                           "content": "Another Claude session sent a message"}}
        self.assertFalse(self.keep(rec))

    def test_assistant_record_dropped(self):
        self.assertFalse(self.keep(assistant("hi")))

    def test_origin_absent_but_prompt_source_present_is_kept(self):
        """Older records predate the origin field; promptSource stands in."""
        rec = human("older turn")
        del rec["origin"]
        self.assertTrue(self.keep(rec))


class TestMachineryPrefixes(unittest.TestCase):
    """Slash commands and injected blocks are typed AT the harness, not prose."""

    def test_slash_command_echo_dropped(self):
        self.assertTrue(mt.is_machinery("<command-name>/model</command-name>"))

    def test_local_command_stdout_dropped(self):
        self.assertTrue(mt.is_machinery("<local-command-stdout>ok</local...>"))

    def test_system_reminder_dropped(self):
        self.assertTrue(mt.is_machinery("<system-reminder>note</system-reminder>"))

    def test_teammate_text_dropped(self):
        self.assertTrue(mt.is_machinery("Another Claude session sent a message:"))

    def test_interrupt_dropped(self):
        self.assertTrue(mt.is_machinery("[Request interrupted by user]"))

    def test_ordinary_prose_kept(self):
        self.assertFalse(mt.is_machinery("I don't understand 'the bound'."))

    def test_leading_whitespace_does_not_smuggle_machinery_through(self):
        self.assertTrue(mt.is_machinery("  <system-reminder>x</system-reminder>"))


class TestPairing(unittest.TestCase):
    """Each turn is paired with the assistant prose that preceded it."""

    def mine(self, records, **kw):
        with tempfile.TemporaryDirectory() as d:
            write_session(d, "proj", "sess", records)
            return mt.mine(d, **kw)

    def test_pairs_with_the_most_recent_assistant_text(self):
        rows = self.mine([assistant("first reply"),
                          assistant("second reply"),
                          human("what is 'it'?")])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["assistant"], "second reply")
        self.assertEqual(rows[0]["human"], "what is 'it'?")

    def test_no_preceding_assistant_gives_empty_prose(self):
        rows = self.mine([human("opening request")])
        self.assertEqual(rows[0]["assistant"], "")

    def test_textless_assistant_turn_does_not_erase_the_prose(self):
        """A reply that is only a tool call has no prose; the last prose stands.

        Without this the corpus loses the stimulus for every complaint that
        followed a tool call, which in practice is most of them.
        """
        toolonly = {"type": "assistant", "timestamp": "2026-08-01T09:59:30Z",
                    "message": {"role": "assistant",
                                "content": [{"type": "tool_use",
                                             "name": "Read"}]}}
        rows = self.mine([assistant("the prose he read"), toolonly,
                          human("this sentence is wrong")])
        self.assertEqual(rows[0]["assistant"], "the prose he read")

    def test_tail_not_head_is_kept(self):
        """The reader stopped near the end of what they had just read."""
        rows = self.mine([assistant("HEADxxxxxxxxxxTAIL"), human("huh?")],
                         tail=4)
        self.assertEqual(rows[0]["assistant"], "TAIL")

    def test_records_carry_project_and_timestamp(self):
        rows = self.mine([human("q", ts="2026-08-02T11:00:00.000Z")])
        self.assertEqual(rows[0]["project"], "proj")
        self.assertEqual(rows[0]["ts"], "2026-08-02T11:00:00.000Z")

    def test_turns_are_numbered_after_sorting(self):
        with tempfile.TemporaryDirectory() as d:
            write_session(d, "p1", "s1", [human("later", ts="2026-08-05T00:00:00Z")])
            write_session(d, "p2", "s2", [human("earlier", ts="2026-08-01T00:00:00Z")])
            rows = mt.mine(d)
        self.assertEqual([r["human"] for r in rows], ["earlier", "later"])
        self.assertEqual([r["n"] for r in rows], [0, 1])

    def test_since_filter_excludes_older_turns(self):
        with tempfile.TemporaryDirectory() as d:
            write_session(d, "p", "s", [human("old", ts="2026-06-01T00:00:00Z"),
                                        human("new", ts="2026-08-01T00:00:00Z")])
            rows = mt.mine(d, since="2026-07-01")
        self.assertEqual([r["human"] for r in rows], ["new"])

    def test_malformed_line_does_not_abort_the_run(self):
        """Transcripts are appended to live; a truncated last line is normal."""
        with tempfile.TemporaryDirectory() as d:
            path = write_session(d, "p", "s", [human("good turn")])
            with open(path, "a") as fh:
                fh.write('{"type": "user", "mess\n')
            rows = mt.mine(d)
        self.assertEqual(len(rows), 1)

    def test_pairing_does_not_leak_across_sessions(self):
        """Two people's sessions, or two of one person's, never cross-pair."""
        with tempfile.TemporaryDirectory() as d:
            write_session(d, "p", "s1", [assistant("prose A",
                                                   ts="2026-08-01T09:00:00Z")])
            write_session(d, "p", "s2", [human("q", ts="2026-08-01T10:00:00Z")])
            rows = mt.mine(d)
        self.assertEqual(rows[0]["assistant"], "")


class TestMain(unittest.TestCase):
    """The command-line contract a Makefile or a shell pipeline depends on."""

    def test_main_writes_jsonl_and_reports_the_count(self):
        with tempfile.TemporaryDirectory() as d:
            write_session(d, "p", "s", [assistant("prose"), human("why?")])
            out = os.path.join(d, "corpus.jsonl")
            code = mt.main(["--root", d, "--out", out])
            self.assertEqual(code, 0)
            rows = [json.loads(l) for l in open(out)]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["human"], "why?")

    def test_empty_corpus_is_an_error_status(self):
        """A silent empty corpus reads as 'nothing to learn'; it is a wrong path."""
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "corpus.jsonl")
            self.assertEqual(mt.main(["--root", d, "--out", out]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
