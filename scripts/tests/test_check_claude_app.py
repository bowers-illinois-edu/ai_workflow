"""Tests for the claude_app staleness checker.

The point of the checker is narrow, and these tests are written to hold it to
that narrow point. The four blocks in `claude_app/` are hand-written
translations of `CLAUDE.md` and `CLAUDE_CODING.md`, so no program can tell
whether their rules still agree with the sources. What a program can tell is
whether the sources have moved since a block was last synced, which is the
signal that a human re-read is owed. Every test below is about that signal:
reading the stamp that records the last sync, checking the right source file
against it, and failing loudly when a block carries no stamp at all.

Stdlib-only and offline: the git log is injected as a callable, so the suite
runs the same way on a machine with no repository.
"""

import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

import check_claude_app as checker


# A header shaped like the real ones: prose, then the stamp, then the rule line
# of dashes, then the text that actually gets pasted into the app.
HEADER_WITH_STAMP = """# Block 2 of 4: Project custom instructions

Make a project for writing work and paste the text below the line into its
custom instructions.

Synced against CLAUDE.md at commit 55ed9ea (2026-08-23).

-------------------------------------------------------------------------------

These rules cover any writing you help me with.
"""

HEADER_WITHOUT_STAMP = """# Block 5 of 5: Something new

Paste the text below the line somewhere.

-------------------------------------------------------------------------------

Some rules.
"""

# A block whose only stamp-looking line sits below the rule line. That text is
# pasted into the app, so a stamp there would be both wrong (it would travel
# into every conversation) and useless as a record. The parser must not see it.
HEADER_WITH_STAMP_BELOW_THE_RULE = """# Block 6 of 6: Mislaid stamp

Paste the text below the line somewhere.

-------------------------------------------------------------------------------

Synced against CLAUDE.md at commit deadbee (2026-08-23).

Some rules.
"""


class ParseStampTests(unittest.TestCase):
    def test_reads_the_source_file_and_the_commit(self):
        stamp = checker.parse_stamp(HEADER_WITH_STAMP)
        self.assertEqual(stamp.source, "CLAUDE.md")
        self.assertEqual(stamp.sha, "55ed9ea")

    def test_returns_none_when_there_is_no_stamp(self):
        # A new block added without a stamp must be reported, not silently
        # treated as current. Returning None is how the checker learns that.
        self.assertIsNone(checker.parse_stamp(HEADER_WITHOUT_STAMP))

    def test_ignores_a_stamp_below_the_rule_line(self):
        self.assertIsNone(checker.parse_stamp(HEADER_WITH_STAMP_BELOW_THE_RULE))

    def test_reads_a_source_other_than_claude_md(self):
        # Block 4 is synced against CLAUDE_CODING.md. If the parser hard-coded
        # CLAUDE.md, block 4 would be checked against a file it does not copy.
        text = HEADER_WITH_STAMP.replace(
            "Synced against CLAUDE.md at commit 55ed9ea",
            "Synced against CLAUDE_CODING.md at commit a500d5f",
        )
        stamp = checker.parse_stamp(text)
        self.assertEqual(stamp.source, "CLAUDE_CODING.md")
        self.assertEqual(stamp.sha, "a500d5f")


class FindStaleTests(unittest.TestCase):
    """`find_stale` takes parsed blocks and a git-log callable and reports the
    blocks whose source has commits after the stamped one."""

    def test_reports_only_the_blocks_whose_source_moved(self):
        blocks = [
            ("claude_app/1_personal_preferences.md", checker.Stamp("CLAUDE.md", "55ed9ea")),
            ("claude_app/4_coding.md", checker.Stamp("CLAUDE_CODING.md", "a500d5f")),
        ]
        commits = {
            ("CLAUDE.md", "55ed9ea"): ["abc1234 Rewrite the compression rules"],
            ("CLAUDE_CODING.md", "a500d5f"): [],
        }
        stale = checker.find_stale(blocks, lambda source, sha: commits[(source, sha)])
        self.assertEqual([path for path, _, _ in stale], ["claude_app/1_personal_preferences.md"])
        self.assertEqual(stale[0][2], ["abc1234 Rewrite the compression rules"])

    def test_asks_the_log_about_each_block_own_source(self):
        # The failure this guards against: checking every block against
        # CLAUDE.md, so that an edit to CLAUDE_CODING.md never flags block 4.
        blocks = [
            ("claude_app/2_project_instructions.md", checker.Stamp("CLAUDE.md", "55ed9ea")),
            ("claude_app/4_coding.md", checker.Stamp("CLAUDE_CODING.md", "a500d5f")),
        ]
        asked = []

        def fake_log(source, sha):
            asked.append((source, sha))
            return []

        checker.find_stale(blocks, fake_log)
        self.assertEqual(
            asked,
            [("CLAUDE.md", "55ed9ea"), ("CLAUDE_CODING.md", "a500d5f")],
        )


class ReportTests(unittest.TestCase):
    def test_names_the_block_the_source_and_every_commit(self):
        stale = [(
            "claude_app/1_personal_preferences.md",
            checker.Stamp("CLAUDE.md", "55ed9ea"),
            ["abc1234 Rewrite the compression rules", "def5678 Add an exemplar"],
        )]
        report = checker.format_report(stale, missing=[])
        self.assertIn("claude_app/1_personal_preferences.md", report)
        self.assertIn("CLAUDE.md", report)
        self.assertIn("abc1234 Rewrite the compression rules", report)
        self.assertIn("def5678 Add an exemplar", report)

    def test_names_blocks_that_carry_no_stamp(self):
        report = checker.format_report([], missing=["claude_app/5_new.md"])
        self.assertIn("claude_app/5_new.md", report)


class ExitCodeTests(unittest.TestCase):
    """`make check-claude-app` is useful only if a stale block fails the build."""

    def test_zero_when_every_block_is_current(self):
        code = checker.main(
            paths=["claude_app/1_personal_preferences.md"],
            commits_for=lambda source, sha: [],
            out=[].append,
            read=lambda path: HEADER_WITH_STAMP,
        )
        self.assertEqual(code, 0)

    def test_nonzero_when_a_block_is_stale(self):
        code = checker.main(
            paths=["claude_app/1_personal_preferences.md"],
            commits_for=lambda source, sha: ["abc1234 Rewrite the compression rules"],
            out=[].append,
            read=lambda path: HEADER_WITH_STAMP,
        )
        self.assertNotEqual(code, 0)

    def test_nonzero_when_a_block_has_no_stamp(self):
        code = checker.main(
            paths=["claude_app/9_unstamped.md"],
            commits_for=lambda source, sha: [],
            out=[].append,
            read=lambda path: HEADER_WITHOUT_STAMP,
        )
        self.assertNotEqual(code, 0)


class RealBlockTests(unittest.TestCase):
    """The invariant that keeps the whole scheme working: every block in the
    repository carries a stamp, and every stamp names a file that exists."""

    def test_the_default_paths_cover_the_skills_as_well_as_the_blocks(self):
        # Two of the app destinations are uploaded skills rather than pasted
        # blocks, and a skill that drifts is exactly as stale as a block that
        # drifts, so both have to be in the list the check walks.
        paths = checker._default_paths()
        self.assertIn(os.path.join("claude_app", "1_personal_preferences.md"), paths)
        self.assertIn(os.path.join("claude_app", "skills", "bowers-prose", "SKILL.md"), paths)
        self.assertIn(os.path.join("claude_app", "skills", "bowers-code", "SKILL.md"), paths)

    def test_every_block_carries_a_stamp_naming_a_real_source_file(self):
        paths = checker._default_paths()
        self.assertTrue(paths, "no blocks found in claude_app/")
        for path in paths:
            with open(os.path.join(REPO_ROOT, path)) as handle:
                stamp = checker.parse_stamp(handle.read())
            self.assertIsNotNone(stamp, "%s carries no sync stamp" % path)
            source = os.path.join(REPO_ROOT, stamp.source)
            self.assertTrue(os.path.exists(source),
                            "%s is stamped against a missing file: %s" % (path, stamp.source))


if __name__ == "__main__":
    unittest.main()
