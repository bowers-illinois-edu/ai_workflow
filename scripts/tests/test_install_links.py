"""Tests for scripts/install_links.py.

The substantive point of the install script is not "does it call ln." It is
that running it on a machine that already has hand-made links must be safe.
The ten links in ~/.claude/skills/ were made by hand over several months, two
of them point at a different repository entirely (.codegpt), and settings.json
sits in the same tree. So the tests below are mostly about what the script
must refuse to touch.

Stdlib only, offline, no network, matching the other suites in this repo.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(REPO, "scripts", "install_links.py")


class InstallLinksTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, "repo")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(os.path.join(self.repo, "skills", "math"))
        os.makedirs(os.path.join(self.repo, "skills", "decks"))
        os.makedirs(os.path.join(self.repo, "output-styles"))
        with open(os.path.join(self.repo, "CLAUDE.md"), "w") as fh:
            fh.write("# global rules\n")
        with open(os.path.join(self.repo, "output-styles", "research.md"), "w") as fh:
            fh.write("# style\n")
        # a zipped copy of a skill lives beside the skill directories and is
        # for the Claude app, not for Claude Code; it must not be linked
        with open(os.path.join(self.repo, "skills", "math.zip"), "w") as fh:
            fh.write("not a skill\n")
        os.makedirs(self.home)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_install(self, *extra):
        return subprocess.run(
            [sys.executable, SCRIPT, "--repo", self.repo, "--home", self.home] + list(extra),
            capture_output=True, text=True)

    def link_target(self, *parts):
        p = os.path.join(self.home, ".claude", *parts)
        return os.readlink(p) if os.path.islink(p) else None

    # --- what it must create -------------------------------------------

    def test_links_each_skill_directory(self):
        self.run_install()
        self.assertEqual(self.link_target("skills", "math"),
                         os.path.join(self.repo, "skills", "math"))
        self.assertEqual(self.link_target("skills", "decks"),
                         os.path.join(self.repo, "skills", "decks"))

    def test_skips_zipped_skills(self):
        self.run_install()
        self.assertFalse(
            os.path.exists(os.path.join(self.home, ".claude", "skills", "math.zip")),
            "the .zip is packaging for the Claude app and is not a skill")

    def test_links_claude_md_and_output_style(self):
        self.run_install()
        self.assertEqual(self.link_target("CLAUDE.md"),
                         os.path.join(self.repo, "CLAUDE.md"))
        self.assertEqual(self.link_target("output-styles", "research.md"),
                         os.path.join(self.repo, "output-styles", "research.md"))

    def test_agents_directory_is_optional(self):
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_links_agents_when_the_directory_exists(self):
        os.makedirs(os.path.join(self.repo, "agents"))
        with open(os.path.join(self.repo, "agents", "first-reader.md"), "w") as fh:
            fh.write("---\nname: first-reader\n---\n")
        self.run_install()
        self.assertEqual(self.link_target("agents", "first-reader.md"),
                         os.path.join(self.repo, "agents", "first-reader.md"))

    # --- what it must not destroy ---------------------------------------

    def test_leaves_a_link_pointing_outside_the_repo_alone(self):
        """Two skills point at ~/.codegpt. A relink would silently steal them."""
        os.makedirs(os.path.join(self.home, ".claude", "skills"))
        foreign = os.path.join(self.tmp, "elsewhere")
        os.makedirs(foreign)
        link = os.path.join(self.home, ".claude", "skills", "math")
        os.symlink(foreign, link)
        r = self.run_install()
        self.assertEqual(os.readlink(link), foreign,
                         "a link into another tree must survive the install")
        self.assertIn("skipped", r.stdout.lower())

    def test_refuses_to_replace_a_real_directory(self):
        os.makedirs(os.path.join(self.home, ".claude", "skills", "math"))
        with open(os.path.join(self.home, ".claude", "skills", "math", "SKILL.md"), "w") as fh:
            fh.write("someone's real work\n")
        r = self.run_install()
        self.assertTrue(os.path.isdir(os.path.join(self.home, ".claude", "skills", "math")))
        self.assertFalse(os.path.islink(os.path.join(self.home, ".claude", "skills", "math")))
        self.assertNotEqual(r.returncode, 0,
                            "a refusal has to be loud, not a line in a log")

    def test_repairs_a_stale_link_into_the_repo(self):
        """A link we own that points at a moved path should be re-pointed."""
        os.makedirs(os.path.join(self.home, ".claude", "skills"))
        link = os.path.join(self.home, ".claude", "skills", "math")
        os.symlink(os.path.join(self.repo, "skills", "gone-away"), link)
        self.run_install()
        self.assertEqual(os.readlink(link), os.path.join(self.repo, "skills", "math"))

    # --- running it twice ------------------------------------------------

    def test_is_idempotent(self):
        first = self.run_install()
        second = self.run_install()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.link_target("skills", "math"),
                         os.path.join(self.repo, "skills", "math"))

    def test_dry_run_creates_nothing(self):
        r = self.run_install("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.home, ".claude", "skills", "math")))
        self.assertIn("would link", r.stdout.lower())


if __name__ == "__main__":
    unittest.main()
