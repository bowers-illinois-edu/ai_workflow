"""Tests for the claude_app staleness checker.

The point of the checker is narrow, and these tests are written to hold it to
that narrow point. The four blocks in `claude_app/` are hand-written
translations of `CLAUDE.md` and `CLAUDE_CODING.md`, so no program can tell
whether their rules still agree with the sources. What a program can tell is
whether the sources have moved since a block was last synced, which is the
signal that a human re-read is owed. Every test below is about that signal:
reading the stamps that record the last sync, checking the right source file
against each, and failing loudly when a block carries no stamp at all.

A block can carry more than one stamp because a block can translate more than
one source. `CLAUDE.md` imports `CLAUDE_WRITING_STANCE.md`, so the two writing
blocks copy rules from both files, and a block stamped against only one of them
would go stale against the other with nothing to report it.

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

# A block translating two sources at once, which is what the writing blocks now
# do: the craft rules come from CLAUDE.md and the verdict rule from
# CLAUDE_WRITING_STANCE.md, and either source can move without the other.
HEADER_WITH_TWO_STAMPS = """# Block 2 of 4: Project custom instructions

Make a project for writing work and paste the text below the line into its
custom instructions.

Synced against CLAUDE.md at commit 55ed9ea (2026-08-23).
Synced against CLAUDE_WRITING_STANCE.md at commit abc1234 (2026-08-29).

-------------------------------------------------------------------------------

These rules cover any writing you help me with.
"""

# One stamp above the rule line and one below it. The one below gets pasted into
# the app, so it is not a record of anything and must not be checked.
HEADER_WITH_SECOND_STAMP_BELOW_THE_RULE = """# Block 7 of 7: Half-mislaid stamp

Paste the text below the line somewhere.

Synced against CLAUDE.md at commit 55ed9ea (2026-08-23).

-------------------------------------------------------------------------------

Synced against CLAUDE_WRITING_STANCE.md at commit deadbee (2026-08-29).

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


class ParseStampsTests(unittest.TestCase):
    def test_reads_the_source_file_and_the_commit(self):
        stamps = checker.parse_stamps(HEADER_WITH_STAMP)
        self.assertEqual([(s.source, s.sha) for s in stamps],
                         [("CLAUDE.md", "55ed9ea")])

    def test_returns_nothing_when_there_is_no_stamp(self):
        # A new block added without a stamp must be reported, not silently
        # treated as current. An empty list is how the checker learns that.
        self.assertEqual(checker.parse_stamps(HEADER_WITHOUT_STAMP), [])

    def test_ignores_a_stamp_below_the_rule_line(self):
        self.assertEqual(checker.parse_stamps(HEADER_WITH_STAMP_BELOW_THE_RULE), [])

    def test_reads_a_source_other_than_claude_md(self):
        # bowers-code is synced against CLAUDE_CODING.md. If the parser
        # hard-coded CLAUDE.md, that block would be checked against a file it
        # does not copy.
        text = HEADER_WITH_STAMP.replace(
            "Synced against CLAUDE.md at commit 55ed9ea",
            "Synced against CLAUDE_CODING.md at commit a500d5f",
        )
        stamps = checker.parse_stamps(text)
        self.assertEqual([(s.source, s.sha) for s in stamps],
                         [("CLAUDE_CODING.md", "a500d5f")])

    def test_reads_every_stamp_in_the_header(self):
        # The failure this guards against: taking the first stamp and stopping,
        # so that a block translating two sources is checked against one of
        # them and rots against the other in silence.
        stamps = checker.parse_stamps(HEADER_WITH_TWO_STAMPS)
        self.assertEqual(
            [(s.source, s.sha) for s in stamps],
            [("CLAUDE.md", "55ed9ea"),
             ("CLAUDE_WRITING_STANCE.md", "abc1234")],
        )

    def test_ignores_a_second_stamp_below_the_rule_line(self):
        # Reading every stamp must not mean reading past the rule line: the
        # text below it is pasted into the app, where a stamp is not a record.
        stamps = checker.parse_stamps(HEADER_WITH_SECOND_STAMP_BELOW_THE_RULE)
        self.assertEqual([(s.source, s.sha) for s in stamps],
                         [("CLAUDE.md", "55ed9ea")])


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

    def test_nonzero_when_only_a_second_source_moved(self):
        # The case this whole change exists for: the block is current with
        # CLAUDE.md and behind CLAUDE_WRITING_STANCE.md. Checking only the
        # first stamp would exit zero and the re-read would never be asked for.
        moved = {"CLAUDE.md": [],
                 "CLAUDE_WRITING_STANCE.md": ["abc1234 Sharpen the verdict rule"]}
        out = []
        code = checker.main(
            paths=["claude_app/1_personal_preferences.md"],
            commits_for=lambda source, sha: moved[source],
            out=out.append,
            read=lambda path: HEADER_WITH_TWO_STAMPS,
        )
        self.assertNotEqual(code, 0)
        self.assertIn("CLAUDE_WRITING_STANCE.md", "\n".join(out))

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
                stamps = checker.parse_stamps(handle.read())
            self.assertTrue(stamps, "%s carries no sync stamp" % path)
            for stamp in stamps:
                source = os.path.join(REPO_ROOT, stamp.source)
                self.assertTrue(
                    os.path.exists(source),
                    "%s is stamped against a missing file: %s" % (path, stamp.source))

    def test_the_blocks_that_translate_the_stance_file_are_stamped_against_it(self):
        # CLAUDE_WRITING_STANCE.md reaches Claude Code through an @-import,
        # which the app cannot follow, so these two blocks translate it by hand.
        # Without a stamp naming it, an edit to that file would never report a
        # re-read as owed, which is the hole this test closes.
        translators = [
            os.path.join("claude_app", "1_personal_preferences.md"),
            os.path.join("claude_app", "skills", "bowers-prose", "SKILL.md"),
        ]
        for path in translators:
            with open(os.path.join(REPO_ROOT, path)) as handle:
                sources = [s.source for s in checker.parse_stamps(handle.read())]
            self.assertIn("CLAUDE_WRITING_STANCE.md", sources,
                          "%s translates the stance file but is not stamped "
                          "against it" % path)



class PhysicalPathTest(unittest.TestCase):
    """A stamp names `skills/math/SKILL.md`, and since 2026-09-02 `skills/` is
    a symlink into plugins/ai-workflow/. Git logs changes at the real path, so
    the checker has to resolve the link before asking git, or every block
    synced against a skill would read as current no matter what changed."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "plugins", "x", "skills", "math"))
        with open(os.path.join(self.tmp, "plugins", "x", "skills", "math", "SKILL.md"), "w") as fh:
            fh.write("rules\n")
        os.symlink(os.path.join("plugins", "x", "skills"), os.path.join(self.tmp, "skills"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_a_path_through_the_symlink_resolves_to_the_plugin_path(self):
        self.assertEqual(checker.physical_path("skills/math/SKILL.md", self.tmp),
                         os.path.join("plugins", "x", "skills", "math", "SKILL.md"))

    def test_a_plain_path_is_returned_unchanged(self):
        self.assertEqual(checker.physical_path("plugins/x/skills/math/SKILL.md", self.tmp),
                         os.path.join("plugins", "x", "skills", "math", "SKILL.md"))

if __name__ == "__main__":
    unittest.main()
