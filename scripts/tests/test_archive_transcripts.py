#!/usr/bin/env python3
"""Unit tests for archive_transcripts.py.

The substantive point of this script is NOT backup. Backblaze already mirrors
the disk, so a dead laptop is covered. What a mirror cannot do is survive
deletion: when Claude Code prunes an old transcript, the mirror eventually
drops it too, and the corpus and the persona both derive from those
transcripts and cannot be rebuilt without them.

So the one property every test here protects is that the archive is ADDITIVE.
It never deletes, and it never overwrites content it cannot prove it still
holds. Three cases follow from that, and each has a test:

  * A source file that grew is an append, which is the normal case for JSONL
    written a line at a time. Replacing the archived copy loses nothing.
  * A source file that did NOT grow but changed is a rewrite or a truncation,
    and replacing the archived copy could lose text. The old copy is snapshot
    under a dated name first.
  * A source file that vanished was pruned. That is exactly the event this
    script exists for, so the archived copy stays.

The archive is also read while Claude Code is writing to the same files, so
reading a partial line must not abort a run.

Run: python3 test_archive_transcripts.py   (or via the repo-root Makefile: make test)
"""

import gzip
import io
import json
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import archive_transcripts as at  # noqa: E402


def write(path, text, mtime=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


def session(src, project, name, text, mtime=None):
    return write(os.path.join(src, project, name + ".jsonl"), text, mtime)


def archived_text(dest, project, name):
    p = os.path.join(dest, "projects", project, name + ".jsonl.gz")
    with gzip.open(p, "rt") as fh:
        return fh.read()


class TestFirstRun(unittest.TestCase):
    def test_copies_and_compresses_into_a_mirrored_tree(self):
        with tempfile.TemporaryDirectory() as d:
            src, dest = os.path.join(d, "src"), os.path.join(d, "dest")
            session(src, "proj-a", "sess1", '{"a":1}\n')
            at.archive(src, dest)
            self.assertEqual(archived_text(dest, "proj-a", "sess1"), '{"a":1}\n')

    def test_round_trip_is_byte_exact(self):
        """An archive that changes the bytes cannot rebuild the corpus."""
        payload = '{"x":"\\u00e9 unicode and \\t tabs"}\n' * 50
        with tempfile.TemporaryDirectory() as d:
            src, dest = os.path.join(d, "src"), os.path.join(d, "dest")
            session(src, "p", "s", payload)
            at.archive(src, dest)
            self.assertEqual(archived_text(dest, "p", "s"), payload)

    def test_destination_tree_is_created(self):
        with tempfile.TemporaryDirectory() as d:
            src, dest = os.path.join(d, "src"), os.path.join(d, "new", "deep")
            session(src, "p", "s", "x\n")
            at.archive(src, dest)
            self.assertTrue(os.path.isdir(os.path.join(dest, "projects", "p")))

    def test_manifest_records_size_hash_and_dates(self):
        with tempfile.TemporaryDirectory() as d:
            src, dest = os.path.join(d, "src"), os.path.join(d, "dest")
            session(src, "p", "s", "hello\n")
            at.archive(src, dest)
            man = json.load(open(os.path.join(dest, "manifest.json")))
            entry = man["files"]["p/s.jsonl"]
            self.assertEqual(entry["size"], 6)
            self.assertEqual(len(entry["sha256"]), 64)
            self.assertIn("first_archived", entry)
            self.assertIn("last_archived", entry)


class TestAdditiveBehaviour(unittest.TestCase):
    """The property the whole script exists for."""

    def test_appended_file_is_re_archived(self):
        with tempfile.TemporaryDirectory() as d:
            src, dest = os.path.join(d, "src"), os.path.join(d, "dest")
            session(src, "p", "s", "line1\n", mtime=1000)
            at.archive(src, dest)
            session(src, "p", "s", "line1\nline2\n", mtime=2000)
            at.archive(src, dest)
            self.assertEqual(archived_text(dest, "p", "s"), "line1\nline2\n")

    def test_unchanged_file_is_skipped(self):
        """Re-compressing 600 MB daily for nothing is the cost to avoid."""
        with tempfile.TemporaryDirectory() as d:
            src, dest = os.path.join(d, "src"), os.path.join(d, "dest")
            session(src, "p", "s", "line1\n", mtime=1000)
            first = at.archive(src, dest)
            second = at.archive(src, dest)
            self.assertEqual(first["archived"], 1)
            self.assertEqual(second["archived"], 0)
            self.assertEqual(second["skipped"], 1)

    def test_shrunken_file_snapshots_the_old_copy_before_overwriting(self):
        """A rewrite could drop text, so the previous archive is preserved."""
        with tempfile.TemporaryDirectory() as d:
            src, dest = os.path.join(d, "src"), os.path.join(d, "dest")
            session(src, "p", "s", "aaa\nbbb\nccc\n", mtime=1000)
            at.archive(src, dest)
            session(src, "p", "s", "zzz\n", mtime=2000)
            at.archive(src, dest)
            self.assertEqual(archived_text(dest, "p", "s"), "zzz\n")
            snaps = [f for f in os.listdir(os.path.join(dest, "projects", "p"))
                     if f.startswith("s.") and f != "s.jsonl.gz"]
            self.assertEqual(len(snaps), 1)
            with gzip.open(os.path.join(dest, "projects", "p", snaps[0]), "rt") as fh:
                self.assertEqual(fh.read(), "aaa\nbbb\nccc\n")

    def test_vanished_source_keeps_its_archived_copy(self):
        """Pruning is the event this script exists to survive."""
        with tempfile.TemporaryDirectory() as d:
            src, dest = os.path.join(d, "src"), os.path.join(d, "dest")
            session(src, "p", "gone", "precious\n")
            at.archive(src, dest)
            os.remove(os.path.join(src, "p", "gone.jsonl"))
            stats = at.archive(src, dest)
            self.assertEqual(archived_text(dest, "p", "gone"), "precious\n")
            self.assertEqual(stats["retained"], 1)

    def test_same_size_different_content_is_treated_as_a_rewrite(self):
        """Equal size is not evidence of an append; hash decides."""
        with tempfile.TemporaryDirectory() as d:
            src, dest = os.path.join(d, "src"), os.path.join(d, "dest")
            session(src, "p", "s", "aaaa\n", mtime=1000)
            at.archive(src, dest)
            session(src, "p", "s", "bbbb\n", mtime=2000)
            at.archive(src, dest)
            snaps = [f for f in os.listdir(os.path.join(dest, "projects", "p"))
                     if f.startswith("s.") and f != "s.jsonl.gz"]
            self.assertEqual(len(snaps), 1)


class TestRobustness(unittest.TestCase):
    def test_unreadable_file_does_not_abort_the_run(self):
        with tempfile.TemporaryDirectory() as d:
            src, dest = os.path.join(d, "src"), os.path.join(d, "dest")
            bad = session(src, "p", "bad", "x\n")
            session(src, "p", "good", "y\n")
            os.chmod(bad, 0o000)
            try:
                stats = at.archive(src, dest)
            finally:
                os.chmod(bad, 0o644)
            self.assertEqual(archived_text(dest, "p", "good"), "y\n")
            self.assertEqual(stats["failed"], 1)

    def test_non_jsonl_files_are_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            src, dest = os.path.join(d, "src"), os.path.join(d, "dest")
            write(os.path.join(src, "p", "notes.txt"), "ignore me\n")
            session(src, "p", "s", "keep\n")
            stats = at.archive(src, dest)
            self.assertEqual(stats["archived"], 1)

    def test_missing_source_is_an_error_not_an_empty_archive(self):
        """A wrong --source must not quietly produce an empty archive."""
        with tempfile.TemporaryDirectory() as d:
            err = io.StringIO()
            import contextlib
            with contextlib.redirect_stderr(err):
                code = at.main(["--source", os.path.join(d, "nope"),
                                "--dest", os.path.join(d, "dest")])
            self.assertEqual(code, 2)


class TestUnreachableDestination(unittest.TestCase):
    """macOS blocks a launchd process from reading ~/Library/CloudStorage.

    A bare background process has none of the Full Disk Access that a terminal
    inherits, so the whole archive directory reads as "Operation not
    permitted". That is a configuration problem with a known fix, and it must
    surface as a clear message rather than a traceback in a log nobody reads.
    """

    def test_unreadable_manifest_does_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            dest = os.path.join(d, "dest")
            os.makedirs(dest)
            man = os.path.join(dest, "manifest.json")
            write(man, "{}")
            os.chmod(man, 0o000)
            try:
                got = at.load_manifest(dest)
            finally:
                os.chmod(man, 0o644)
            self.assertEqual(got, {"files": {}})

    def test_unwritable_destination_exits_two_and_names_the_cause(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "src")
            session(src, "p", "s", "x\n")
            dest = os.path.join(d, "locked", "dest")
            os.makedirs(os.path.dirname(dest))
            os.chmod(os.path.dirname(dest), 0o500)
            err = io.StringIO()
            import contextlib
            try:
                with contextlib.redirect_stderr(err):
                    code = at.main(["--source", src, "--dest", dest])
            finally:
                os.chmod(os.path.dirname(dest), 0o755)
            self.assertEqual(code, 2)
            self.assertIn("Full Disk Access", err.getvalue())


class TestDefaultDestination(unittest.TestCase):
    """Same rule as the corpus miner, and for the same reason.

    macOS denies a launchd job access to ~/Library/CloudStorage, so a default
    inside Dropbox would fail every night while working by hand. A plain home
    directory works for background jobs and is covered by whole-disk backup.
    """

    def test_environment_variable_wins(self):
        env = {"CLAUDE_TRANSCRIPT_ARCHIVE": "/elsewhere"}
        self.assertEqual(at.default_archive_path(env=env, home="/h"), "/elsewhere")

    def test_default_is_under_the_home_directory(self):
        self.assertTrue(at.default_archive_path(env={}, home="/h").startswith("/h/"))

    def test_default_avoids_the_protected_cloud_storage_path(self):
        got = at.default_archive_path(env={}, home="/h")
        self.assertNotIn("CloudStorage", got)
        self.assertNotIn("Dropbox", got)

    def test_default_needs_no_directory_to_exist_yet(self):
        self.assertIsNotNone(at.default_archive_path(env={}, home="/nonexistent"))


class TestMain(unittest.TestCase):
    def test_reports_a_summary_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as d:
            src, dest = os.path.join(d, "src"), os.path.join(d, "dest")
            session(src, "p", "s", "x\n")
            err = io.StringIO()
            import contextlib
            with contextlib.redirect_stderr(err):
                code = at.main(["--source", src, "--dest", dest])
            self.assertEqual(code, 0)
            self.assertIn("archived", err.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
