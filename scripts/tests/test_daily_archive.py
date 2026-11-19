#!/usr/bin/env python3
"""End-to-end tests for daily_archive.sh, the job launchd runs each morning.

The job does two things in order: archive_transcripts.py copies every
session in ~/.claude/projects into ~/Claude_Transcript_Archive, and
mine_transcripts.py rebuilds corpus.jsonl, the file that pairs each reply
with the next thing Jake typed. The point of having an archive at all is that
Claude Code deletes old sessions from ~/.claude/projects. So the one property
these tests protect is that a turn Jake typed stays in the corpus after
Claude Code has deleted the session it came from.

Until 2026-11-19 it did not. The job built the corpus from
~/.claude/projects, and on that day the corpus held no rows for August or
September 2026, although the archive held every session from both months.
Those months are the baseline for any comparison of Jake's stops across a
model change, and the months the first-reader persona was built from.

Each test runs the real script under a temporary HOME, so nothing in the
real archive, corpus, or log is touched.

Run: python3 test_daily_archive.py   (or via the repo-root Makefile: make test)
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(REPO, "scripts", "daily_archive.sh")


def session(home, project, name, typed, ts):
    """One live Claude Code session: a reply, then one turn Jake typed."""
    proj = os.path.join(home, ".claude", "projects", project)
    os.makedirs(proj, exist_ok=True)
    records = [
        {"type": "assistant", "timestamp": ts,
         "message": {"role": "assistant",
                     "content": [{"type": "text", "text": "a reply"}]}},
        {"type": "user", "timestamp": ts, "origin": {"kind": "human"},
         "message": {"role": "user", "content": typed}},
    ]
    with open(os.path.join(proj, name + ".jsonl"), "w") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


def run_job(home, extra_env=None, check=True):
    env = {"HOME": home, "PATH": os.environ["PATH"]}
    env.update(extra_env or {})
    return subprocess.run(["bash", SCRIPT], env=env, check=check, timeout=60)


def corpus_turns(path):
    with open(path) as fh:
        return [json.loads(l)["human"] for l in fh]


class TestPrunedSessionsStayInTheCorpus(unittest.TestCase):

    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.corpus = os.path.join(self.home, "Claude_Transcript_Archive",
                                   "corpus.jsonl")

    def tearDown(self):
        shutil.rmtree(self.home)

    def test_august_turn_survives_claude_code_deleting_its_session(self):
        """The bug of 2026-11-19, in miniature: an August session is archived,
        Claude Code deletes it, and a November session arrives. The corpus
        must hold both turns."""
        session(self.home, "proj", "aug", "I don't understand 'the bound'",
                "2026-08-20T10:00:00Z")
        run_job(self.home)
        os.remove(os.path.join(self.home, ".claude", "projects", "proj",
                               "aug.jsonl"))
        session(self.home, "proj", "nov", "too long",
                "2026-11-18T10:00:00Z")
        run_job(self.home)
        self.assertEqual(corpus_turns(self.corpus),
                         ["I don't understand 'the bound'", "too long"])

    def test_each_turn_appears_once_after_repeated_runs(self):
        """The job runs every day over an archive that keeps every session,
        so a turn must not be counted again on each run."""
        session(self.home, "proj", "aug", "what does 'the family' mean?",
                "2026-08-20T10:00:00Z")
        for _ in range(3):
            run_job(self.home)
        self.assertEqual(corpus_turns(self.corpus),
                         ["what does 'the family' mean?"])

    def test_every_turn_ever_typed_is_in_the_corpus_once(self):
        """The property the monthly check depends on, over several projects
        and months, with Claude Code deleting sessions between nightly runs:
        the corpus holds exactly the turns Jake typed, each once."""
        typed = []
        live = os.path.join(self.home, ".claude", "projects")
        plan = [  # (project, session, month) written before each night's run
            [("paper", "jun", "2026-06"), ("pkg", "aug1", "2026-08")],
            [("paper", "aug2", "2026-08"), ("course", "sep", "2026-09")],
            [("pkg", "oct", "2026-10")],
            [("paper", "nov", "2026-11"), ("course", "nov", "2026-11")],
        ]
        for night, sessions in enumerate(plan):
            for project, name, month in sessions:
                text = "what does '%s %s' mean?" % (project, name)
                session(self.home, project, name, text, month + "-15T10:00:00Z")
                typed.append(text)
            run_job(self.home)
            # Claude Code deletes the oldest sessions after the archive ran.
            if night == 1:
                os.remove(os.path.join(live, "paper", "jun.jsonl"))
                os.remove(os.path.join(live, "pkg", "aug1.jsonl"))
            if night == 2:
                os.remove(os.path.join(live, "course", "sep.jsonl"))
        self.assertEqual(sorted(corpus_turns(self.corpus)), sorted(typed))

    def test_job_fails_and_names_the_month_when_archiving_fails(self):
        """If the archive step cannot write, today's turn reaches neither the
        archive nor the corpus. The job must exit with an error, and its log
        must name the month that is short, so the loss is not silent."""
        blocked = os.path.join(self.home, "not_a_folder")
        open(blocked, "w").close()
        env = {"CLAUDE_TRANSCRIPT_ARCHIVE": blocked,
               "FIRST_READER_CORPUS": os.path.join(self.home, "corpus.jsonl")}
        session(self.home, "proj", "nov", "too long", "2026-11-18T10:00:00Z")
        result = run_job(self.home, env, check=False)
        self.assertNotEqual(result.returncode, 0)
        with open(os.path.join(self.home, "Library", "Logs",
                               "claude-archive.log")) as fh:
            self.assertIn("2026-11", fh.read())

    def notifier(self):
        """A stand-in for the Mac notification: a command that writes each
        argument it is given on its own line, so the test can read what Jake
        would have seen and what a click would open. The job runs
        $CLAUDE_ARCHIVE_NOTIFY with two arguments, the message and the note
        to open on a click, when it is set, and terminal-notifier otherwise."""
        seen = os.path.join(self.home, "notified.txt")
        cmd = os.path.join(self.home, "notify.sh")
        with open(cmd, "w") as fh:
            fh.write('#!/bin/bash\nprintf "%%s\\n" "$@" >> "%s"\n' % seen)
        os.chmod(cmd, 0o755)
        return cmd, seen

    def fail_archiving(self, extra_env=None):
        """Run the job with the archive step unable to write, after one
        session typed in November, so November comes up short."""
        blocked = os.path.join(self.home, "not_a_folder")
        open(blocked, "w").close()
        env = {"CLAUDE_TRANSCRIPT_ARCHIVE": blocked,
               "FIRST_READER_CORPUS": os.path.join(self.home, "corpus.jsonl")}
        env.update(extra_env or {})
        session(self.home, "proj", "nov", "too long", "2026-11-18T10:00:00Z")
        return run_job(self.home, env, check=False)

    def test_short_month_sends_a_notification_and_writes_the_check_file(self):
        """Jake chose on 2026-11-19 to hear about a short month by a Mac
        notification and in the today skill. The today skill reads
        corpus_check.txt, which sits beside the corpus."""
        cmd, seen = self.notifier()
        self.fail_archiving({"CLAUDE_ARCHIVE_NOTIFY": cmd})
        with open(seen) as fh:
            self.assertIn("2026-11", fh.read())
        with open(os.path.join(self.home, "corpus_check.txt")) as fh:
            self.assertIn("2026-11", fh.read())

    def test_clicking_the_notification_opens_a_note_that_says_what_to_do(self):
        """Jake, 2026-11-19: when he clicks a notification he wants to land
        where his next action is clear. So the job writes a note in his
        Obsidian vault naming the short month and the one thing to do, and
        the notification opens that note when clicked."""
        vault = os.path.join(self.home, "Documents", "Obsidian Vault")
        os.makedirs(vault)
        cmd, seen = self.notifier()
        self.fail_archiving({"CLAUDE_ARCHIVE_NOTIFY": cmd})
        note = os.path.join(vault, "transcript_corpus_check.md")
        with open(note) as fh:
            text = fh.read()
        self.assertIn("2026-11", text)
        # The next action: a Claude Code session in the repository that
        # holds the job, given the two files that say what went wrong.
        self.assertIn("cd ~/repos/ai_workflow", text)
        self.assertIn("corpus_check.txt", text)
        self.assertIn("claude-archive.log", text)
        with open(seen) as fh:
            self.assertEqual(fh.read().splitlines()[-1], note)

    def test_note_goes_beside_the_corpus_when_there_is_no_vault(self):
        """A collaborator's machine has no Obsidian vault at Jake's path."""
        cmd, seen = self.notifier()
        self.fail_archiving({"CLAUDE_ARCHIVE_NOTIFY": cmd})
        note = os.path.join(self.home, "transcript_corpus_check.md")
        self.assertTrue(os.path.exists(note))

    def test_no_notification_and_an_empty_check_file_when_nothing_is_short(self):
        cmd, seen = self.notifier()
        session(self.home, "proj", "aug", "I'm confused", "2026-08-20T10:00:00Z")
        run_job(self.home, {"CLAUDE_ARCHIVE_NOTIFY": cmd})
        self.assertFalse(os.path.exists(seen))
        with open(os.path.join(self.home, "Claude_Transcript_Archive",
                               "corpus_check.txt")) as fh:
            self.assertEqual(fh.read(), "")

    def test_note_is_removed_once_nothing_is_short(self):
        """A note left from a fixed problem would send Jake to fix it again."""
        vault = os.path.join(self.home, "Documents", "Obsidian Vault")
        os.makedirs(vault)
        note = os.path.join(vault, "transcript_corpus_check.md")
        with open(note, "w") as fh:
            fh.write("old warning\n")
        cmd, seen = self.notifier()
        session(self.home, "proj", "aug", "I'm confused", "2026-08-20T10:00:00Z")
        run_job(self.home, {"CLAUDE_ARCHIVE_NOTIFY": cmd})
        self.assertFalse(os.path.exists(note))

    def test_archive_moved_by_environment_variable_is_the_one_read(self):
        """archive_transcripts.py writes to $CLAUDE_TRANSCRIPT_ARCHIVE when it
        is set, so the corpus has to be built from that same place."""
        elsewhere = os.path.join(self.home, "elsewhere")
        env = {"CLAUDE_TRANSCRIPT_ARCHIVE": elsewhere,
               "FIRST_READER_CORPUS": os.path.join(elsewhere, "corpus.jsonl")}
        session(self.home, "proj", "aug", "I'm confused",
                "2026-08-20T10:00:00Z")
        run_job(self.home, env)
        os.remove(os.path.join(self.home, ".claude", "projects", "proj",
                               "aug.jsonl"))
        session(self.home, "proj", "nov", "too long", "2026-11-18T10:00:00Z")
        run_job(self.home, env)
        self.assertEqual(
            corpus_turns(os.path.join(elsewhere, "corpus.jsonl")),
            ["I'm confused", "too long"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
