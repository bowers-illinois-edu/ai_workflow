"""Tests for scripts/build_agents_md.py, which writes codex/AGENTS.md.

Codex reads one instruction file, ~/.codex/AGENTS.md, and follows no import
lines. CLAUDE.md pulls in two files with lines that begin with "@", so the
symlink from ~/.codex/AGENTS.md to CLAUDE.md that this machine has carried
since 2026-08-06 hands Codex the writing rules and a bare path where the
coding rules and the writing stance should be. The build writes the imported
files out in place, so Codex reads the same rules Claude Code reads.

The output is a transcription rather than a translation, so the tests can
hold the tracked file to byte equality with a fresh build. That is stricter
than the stamp check the hand-written app blocks get, and it is possible
here only because nothing is reworded.

Stdlib only, offline.
"""

import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

import build_agents_md as builder


CLAUDE_MD = """# CLAUDE.md

Rules that apply everywhere.

@~/repos/ai_workflow/CODING.md

## Writing

More rules.

@/somewhere/that/does/not/exist/STANCE.md

The end.
"""

CODING = "## Coding rules\n\nWrite the tests first.\n"
STANCE = "# Report what happened\n\nNot your verdict on it.\n"


class BuildAgentsMdTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        self.put("CLAUDE.md", CLAUDE_MD)
        self.put("CODING.md", CODING)
        self.put("STANCE.md", STANCE)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def put(self, name, text):
        with open(os.path.join(self.repo, name), "w", encoding="ascii") as fh:
            fh.write(text)

    def read(self, *parts):
        with open(os.path.join(self.repo, *parts), encoding="ascii") as fh:
            return fh.read()

    # --- what the build contains ------------------------------------------

    def test_each_import_line_is_replaced_by_the_file_it_names(self):
        out = builder.build(self.repo)
        self.assertNotIn("@~/", out)
        self.assertNotIn("@/somewhere", out)
        self.assertIn(CODING.strip(), out)
        self.assertIn(STANCE.strip(), out)
        # the imported text sits where the @ line sat, so the order of the
        # surrounding prose is preserved
        self.assertLess(out.index("Rules that apply everywhere."), out.index(CODING.strip()))
        self.assertLess(out.index(CODING.strip()), out.index("## Writing"))
        self.assertLess(out.index("## Writing"), out.index(STANCE.strip()))
        self.assertLess(out.index(STANCE.strip()), out.index("The end."))

    def test_import_resolves_by_basename_in_the_repository(self):
        """The @ lines carry this laptop's absolute paths. A clone elsewhere
        has the same files under the repository root, and that is where the
        build reads them, so the second @ line above resolves although the
        path it names exists on no machine."""
        out = builder.build(self.repo)
        self.assertIn(STANCE.strip(), out)

    def test_missing_import_is_an_error_not_a_silent_gap(self):
        self.put("CLAUDE.md", "top\n\n@~/elsewhere/GONE.md\n\nbottom\n")
        with self.assertRaises(builder.MissingImport):
            builder.build(self.repo)

    def test_a_non_ascii_source_stops_the_build_and_names_the_file(self):
        """Found on 2026-09-02: CLAUDE_CODING.md carried a unicode arrow in a
        version-bump example, against the rule in CLAUDE.md. The build must
        say which file and line rather than die in the codec."""
        with open(os.path.join(self.repo, "CODING.md"), "wb") as fh:
            fh.write(b"## Coding rules\n\nbump 0.0.3.0 \xe2\x86\x92 0.0.3.1\n")
        with self.assertRaises(builder.NonAscii) as caught:
            builder.build(self.repo)
        self.assertIn("CODING.md", str(caught.exception))
        self.assertIn("line 3", str(caught.exception))

    def test_marker_lines_name_the_imported_file_around_its_content(self):
        out = builder.build(self.repo)
        begin = out.index("Begin CODING.md")
        end = out.index("End CODING.md")
        self.assertLess(begin, out.index(CODING.strip()))
        self.assertLess(out.index(CODING.strip()), end)

    def test_header_says_generated_and_how_to_read_it(self):
        out = builder.build(self.repo)
        head = out[:1200]
        self.assertIn("scripts/build_agents_md.py", head)
        self.assertIn("Do not edit", head)
        self.assertIn("Codex", head)
        self.assertIn("~/.codex/skills", head)
        # the header comes before any of CLAUDE.md's own text
        self.assertLess(out.index("Do not edit"), out.index("# CLAUDE.md"))

    def test_output_is_ascii(self):
        builder.build(self.repo).encode("ascii")

    # --- writing and checking the tracked file ----------------------------

    def test_write_puts_the_build_at_codex_agents_md(self):
        builder.write(self.repo)
        self.assertEqual(self.read("codex", "AGENTS.md"), builder.build(self.repo))

    def test_check_fails_when_the_tracked_file_is_stale(self):
        builder.write(self.repo)
        self.assertTrue(builder.check(self.repo))
        self.put("CLAUDE.md", CLAUDE_MD + "\nA new rule.\n")
        self.assertFalse(builder.check(self.repo))
        builder.write(self.repo)
        self.assertTrue(builder.check(self.repo))

    def test_check_fails_when_the_tracked_file_is_missing(self):
        self.assertFalse(builder.check(self.repo))

    def test_main_check_exits_nonzero_when_stale(self):
        builder.write(self.repo)
        self.put("CLAUDE.md", CLAUDE_MD + "\nA new rule.\n")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = builder.main(["--repo", self.repo, "--check"])
        self.assertNotEqual(code, 0)

    def test_main_warns_when_the_file_exceeds_codex_default_budget(self):
        """Codex reads at most project_doc_max_bytes of instructions, 32 KiB
        by default, and truncates the rest without a word. The real build
        is above that, so the warning has to name the setting to change."""
        self.put("CLAUDE.md", CLAUDE_MD + ("x" * 80 + "\n") * 420)
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = builder.main(["--repo", self.repo])
        self.assertEqual(code, 0)
        self.assertIn("32768", err.getvalue())
        self.assertIn("project_doc_max_bytes", err.getvalue())

    def test_main_is_quiet_below_the_budget(self):
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            builder.main(["--repo", self.repo])
        self.assertEqual(err.getvalue(), "")


class TrackedOutputTest(unittest.TestCase):
    """The drift test on the real repository. `make test` runs it, so an
    edit to CLAUDE.md or either imported file without `make agents-md`
    fails here rather than reaching Codex silently."""

    def test_tracked_codex_agents_md_matches_a_fresh_build(self):
        path = os.path.join(REPO_ROOT, "codex", "AGENTS.md")
        self.assertTrue(os.path.isfile(path), "codex/AGENTS.md is not built")
        with open(path, encoding="ascii") as fh:
            self.assertEqual(fh.read(), builder.build(REPO_ROOT))


if __name__ == "__main__":
    unittest.main()
