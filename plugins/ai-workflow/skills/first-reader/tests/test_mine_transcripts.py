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

import contextlib
import gzip
import io
import json
import os
import sys
import tempfile
import time
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


def assistant(text, ts="2026-08-01T09:59:00.000Z", model="claude-opus-5"):
    return {"type": "assistant", "timestamp": ts,
            "message": {"role": "assistant", "model": model,
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


def write_gz_session(dirpath, project, name, records):
    """Write records the way archive_transcripts.py stores them: gzipped,
    under <dirpath>/<project>/<name>.jsonl.gz."""
    proj = os.path.join(dirpath, project)
    os.makedirs(proj, exist_ok=True)
    path = os.path.join(proj, name + ".jsonl.gz")
    with gzip.open(path, "wt") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    return path


class TestReadingTheArchive(unittest.TestCase):
    """The corpus must be buildable from the archive, not only from
    ~/.claude/projects.

    Claude Code deletes old sessions from ~/.claude/projects, so a corpus
    built from there loses its oldest months. On 2026-11-19 it held no rows
    for August or September 2026, which are the months Jake's stops are
    compared against when a model changes, and the months the persona was
    built from. The archive keeps every session, gzipped, so the miner has
    to read the gzipped copies and give the same rows it would give from
    the originals.
    """

    RECORDS = [assistant("the prose he read", ts="2026-08-20T09:59:00Z"),
               human("what does 'the bound' mean?", ts="2026-08-20T10:00:00Z")]

    def test_gzipped_session_gives_the_same_rows_as_the_original(self):
        with tempfile.TemporaryDirectory() as live, \
                tempfile.TemporaryDirectory() as arch:
            write_session(live, "proj", "sess", self.RECORDS)
            write_gz_session(arch, "proj", "sess", self.RECORDS)
            self.assertEqual(mt.mine(live), mt.mine(arch))

    def test_session_name_drops_both_extensions(self):
        """The session id joins a row to the model that wrote the reply, so
        it must be the bare id, not 'sess.jsonl'."""
        with tempfile.TemporaryDirectory() as arch:
            write_gz_session(arch, "proj", "sess", self.RECORDS)
            rows = mt.mine(arch)
        self.assertEqual(rows[0]["session"], "sess")

    def test_rewritten_session_keeps_turns_from_the_older_copy_once(self):
        """When a session file changes without growing, the archive keeps the
        old copy as <session>.<date>.jsonl.gz before replacing it, because the
        rewrite may have dropped text. A turn that survives only in the old
        copy is still one of Jake's turns, so it belongs in the corpus. A turn
        in both copies is one turn and appears once.
        """
        both = human("in both copies", ts="2026-08-20T10:00:00Z")
        old_only = human("only in the old copy", ts="2026-08-20T11:00:00Z")
        new_only = human("only in the new copy", ts="2026-08-20T12:00:00Z")
        with tempfile.TemporaryDirectory() as arch:
            write_gz_session(arch, "proj", "sess.2026-08-21", [both, old_only])
            write_gz_session(arch, "proj", "sess", [both, new_only])
            rows = mt.mine(arch)
        self.assertEqual([r["human"] for r in rows],
                         ["in both copies", "only in the old copy",
                          "only in the new copy"])
        self.assertEqual({r["session"] for r in rows}, {"sess"})

    def test_subagent_transcripts_are_not_read(self):
        """The archive also holds each subagent's transcript under
        <project>/<session>/subagents/. A 'user' turn there is a prompt one
        agent wrote to another, not something Jake typed."""
        with tempfile.TemporaryDirectory() as arch:
            write_gz_session(arch, "proj", "sess", self.RECORDS)
            write_gz_session(arch, os.path.join("proj", "sess", "subagents"),
                             "agent-a1", [human("an agent's prompt")])
            rows = mt.mine(arch)
        self.assertEqual([r["human"] for r in rows],
                         ["what does 'the bound' mean?"])

    def test_damaged_gzip_file_does_not_stop_the_other_sessions(self):
        """One unreadable file must not keep every other session out of the corpus."""
        with tempfile.TemporaryDirectory() as arch:
            write_gz_session(arch, "proj", "good", self.RECORDS)
            path = write_gz_session(arch, "proj", "bad", self.RECORDS)
            with open(path, "rb") as fh:
                data = fh.read()
            with open(path, "wb") as fh:
                fh.write(data[: len(data) // 2])
            rows = mt.mine(arch)
        self.assertIn("good", {r["session"] for r in rows})


class TestModelOfTheReply(unittest.TestCase):
    """Each row names the model that wrote the reply Jake's turn answers.

    The monthly check compares Jake's stop share between models, so a row
    without its model cannot be used there. The model is the one that wrote
    the prose in the row, which is not always the model of the last record
    before the turn: a tool call with no prose can come in between.
    """

    def mine(self, records):
        with tempfile.TemporaryDirectory() as d:
            write_session(d, "proj", "sess", records)
            return mt.mine(d)

    def test_row_names_the_model_that_wrote_the_reply(self):
        rows = self.mine([assistant("a reply", model="claude-opus-5-5"),
                          human("what does 'the bound' mean?")])
        self.assertEqual(rows[0]["model"], "claude-opus-5-5")

    def test_model_comes_from_the_prose_not_a_later_tool_call(self):
        """The model switched between the prose and a tool call. The prose
        is what Jake read, so its model is the one recorded."""
        toolonly = {"type": "assistant", "timestamp": "2026-08-01T09:59:30Z",
                    "message": {"role": "assistant", "model": "claude-fable-5",
                                "content": [{"type": "tool_use",
                                             "name": "Read"}]}}
        rows = self.mine([assistant("the prose he read", model="claude-opus-5"),
                          toolonly, human("this sentence is wrong")])
        self.assertEqual(rows[0]["model"], "claude-opus-5")

    def test_turn_with_no_reply_before_it_has_no_model(self):
        rows = self.mine([human("opening request")])
        self.assertEqual(rows[0]["model"], "")


class TestCorpusCheck(unittest.TestCase):
    """The nightly job compares the corpus with the transcripts, month by month.

    A made-up archive in a test cannot catch the next way the real corpus
    loses turns, so the job counts Jake's turns per month on his real data
    every night and reports any month where the counts differ. Two sources
    are compared with the corpus, and each catches a different failure:

      * the archive, which holds every session ever kept: a month with fewer
        turns in the corpus than in the archive means the corpus was built
        from the wrong place, which is the failure of 2026-11-19;
      * Claude Code's own folder: a month with more turns there than in the
        corpus means the archive step failed and the corpus is falling
        behind, as happened when macOS denied the job access to Dropbox.
    """

    def corpus_from(self, root, path):
        with open(path, "w") as fh:
            for row in mt.mine(root):
                fh.write(json.dumps(row) + "\n")

    def test_corpus_built_from_the_archive_reports_no_difference(self):
        with tempfile.TemporaryDirectory() as live, \
                tempfile.TemporaryDirectory() as arch:
            write_session(live, "p", "nov", [human("x", ts="2026-11-02T00:00:00Z")])
            write_gz_session(arch, "p", "aug", [human("y", ts="2026-08-02T00:00:00Z")])
            write_gz_session(arch, "p", "nov", [human("x", ts="2026-11-02T00:00:00Z")])
            corpus = os.path.join(arch, "corpus.jsonl")
            self.corpus_from(arch, corpus)
            self.assertEqual(mt.check_corpus(corpus, arch, live), [])

    def test_month_in_the_archive_but_missing_from_the_corpus_is_reported(self):
        """The corpus was built from Claude Code's folder, which no longer has
        August. The report names the month and both counts."""
        with tempfile.TemporaryDirectory() as live, \
                tempfile.TemporaryDirectory() as arch:
            write_session(live, "p", "nov", [human("x", ts="2026-11-02T00:00:00Z")])
            write_gz_session(arch, "p", "aug", [human("y", ts="2026-08-02T00:00:00Z"),
                                                human("z", ts="2026-08-03T00:00:00Z")])
            write_gz_session(arch, "p", "nov", [human("x", ts="2026-11-02T00:00:00Z")])
            corpus = os.path.join(arch, "corpus.jsonl")
            self.corpus_from(live, corpus)
            self.assertEqual(mt.check_corpus(corpus, arch, live),
                             [("2026-08", "archive", 2, 0)])

    def test_turn_in_claude_codes_folder_but_missing_from_the_corpus_is_reported(self):
        """The archive step failed, so today's session never reached the
        archive or the corpus built from it."""
        with tempfile.TemporaryDirectory() as live, \
                tempfile.TemporaryDirectory() as arch:
            write_gz_session(arch, "p", "aug", [human("y", ts="2026-08-02T00:00:00Z")])
            write_session(live, "p", "nov", [human("x", ts="2026-11-02T00:00:00Z")])
            corpus = os.path.join(arch, "corpus.jsonl")
            self.corpus_from(arch, corpus)
            self.assertEqual(mt.check_corpus(corpus, arch, live),
                             [("2026-11", "live", 1, 0)])

    def test_turn_typed_after_the_corpus_was_written_is_not_reported(self):
        """The job runs at 9:30, often while Jake is working. A turn he types
        after the corpus was written is not missing from it, so it must not
        set off a notification."""
        with tempfile.TemporaryDirectory() as live, \
                tempfile.TemporaryDirectory() as arch:
            write_gz_session(arch, "p", "aug", [human("y", ts="2026-08-02T00:00:00Z")])
            corpus = os.path.join(arch, "corpus.jsonl")
            self.corpus_from(arch, corpus)
            written = os.path.getmtime(corpus)
            later = time.strftime("%Y-%m-%dT%H:%M:%S.000Z",
                                  time.gmtime(written + 60))
            write_session(live, "p", "now", [human("typed after", ts=later)])
            self.assertEqual(mt.check_corpus(corpus, arch, live), [])

    def test_check_flag_sets_the_exit_status(self):
        """The nightly job reads the exit status, so a difference must make
        the command fail, and no difference must let it succeed."""
        with tempfile.TemporaryDirectory() as live, \
                tempfile.TemporaryDirectory() as arch:
            write_gz_session(arch, "p", "aug", [human("y", ts="2026-08-02T00:00:00Z")])
            os.makedirs(os.path.join(live, "p"))
            good = os.path.join(arch, "good.jsonl")
            self.corpus_from(arch, good)
            empty = os.path.join(arch, "empty.jsonl")
            open(empty, "w").close()
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(mt.main(["--check", good, "--root", arch,
                                          "--live", live]), 0)
                self.assertEqual(mt.main(["--check", empty, "--root", arch,
                                          "--live", live]), 1)


class TestDefaultCorpusLocation(unittest.TestCase):
    """Where the corpus goes when --out is not given.

    It must not go in either repository, because it spans every project and
    holds other people's unpublished work, students' job materials,
    confidential peer reviews, and medical notes. It also must not go under
    ~/Library/CloudStorage: macOS denies a launchd job access there, so the
    daily refresh would fail silently every night while working by hand.

    So the default is a plain directory in the home folder, which any
    background job can write and which whole-disk backup already covers.
    """

    def test_environment_variable_wins(self):
        env = {"FIRST_READER_CORPUS": "/somewhere/else/corpus.jsonl"}
        self.assertEqual(mt.default_corpus_path(env=env, home="/home/x"),
                         "/somewhere/else/corpus.jsonl")

    def test_environment_variable_is_tilde_expanded(self):
        got = mt.default_corpus_path(env={"FIRST_READER_CORPUS": "~/mine.jsonl"},
                                     home="/home/x")
        self.assertTrue(got.endswith("/mine.jsonl"))
        self.assertNotIn("~", got)

    def test_default_is_under_the_home_directory(self):
        got = mt.default_corpus_path(env={}, home="/home/x")
        self.assertTrue(got.startswith("/home/x/"))
        self.assertTrue(got.endswith("corpus.jsonl"))

    def test_default_avoids_the_protected_cloud_storage_path(self):
        """A launchd job cannot write there, so the default must never be it."""
        got = mt.default_corpus_path(env={}, home="/home/x")
        self.assertNotIn("CloudStorage", got)
        self.assertNotIn("Dropbox", got)

    def test_default_needs_no_directory_to_exist_yet(self):
        """A fresh machine has nothing; the caller creates the parent."""
        self.assertIsNotNone(mt.default_corpus_path(env={}, home="/nonexistent"))


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

    def test_out_directory_is_created_if_missing(self):
        """A fresh machine has no archive directory yet."""
        with tempfile.TemporaryDirectory() as d:
            write_session(d, "p", "s", [assistant("prose"), human("why?")])
            out = os.path.join(d, "new", "nested", "corpus.jsonl")
            self.assertEqual(mt.main(["--root", d, "--out", out]), 0)
            self.assertTrue(os.path.exists(out))

    def test_empty_corpus_is_an_error_status(self):
        """A silent empty corpus reads as 'nothing to learn'; it is a wrong path."""
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "corpus.jsonl")
            self.assertEqual(mt.main(["--root", d, "--out", out]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
