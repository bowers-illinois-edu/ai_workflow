"""The plugin directories must hold real files, not symlinks.

Codex installs a plugin by copying plugins/<name>/ out of a git snapshot of
this repository, and the copy does not follow symlinks. On 2026-09-02 the
copies under ~/.codex/plugins/cache/ai-workflow/ held no skills and an empty
commands directory, because plugins/ai-workflow/skills,
plugins/ai-workflow-app/skills, and plugins/ai-workflow/commands/handoff.md
are all symlinks that point outside their plugin. ChatGPT installs plugins
by the same route. Claude Code's installer follows the links, which is why
the gap showed up nowhere until the cache was read.

So the first test is blunt: no symlink anywhere under plugins/. The rest say
what has to be true once the real files live there. The Claude Code skills
and the plugin's copy of them are the same bytes, the app plugin's copy of
the scanner and of the math references match the originals, and the handoff
command is a real file. Where a directory has to exist twice, byte equality
is what turns drift into a failing test.

Stdlib only, offline.
"""

import filecmp
import os
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLUGINS = os.path.join(REPO_ROOT, "plugins")
IGNORE = {"__pycache__", ".DS_Store"}


def symlinks_under(root):
    found = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in dirnames + filenames:
            path = os.path.join(dirpath, name)
            if os.path.islink(path):
                found.append(os.path.relpath(path, REPO_ROOT))
    return sorted(found)


def files_under(root):
    """Relative paths of every regular file, skipping caches."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE]
        for name in filenames:
            if name not in IGNORE:
                out.append(os.path.relpath(os.path.join(dirpath, name), root))
    return sorted(out)


def assert_same_tree(test, left, right):
    test.assertTrue(os.path.isdir(left), left)
    test.assertTrue(os.path.isdir(right), right)
    test.assertEqual(files_under(left), files_under(right),
                     "different file lists under %s and %s" % (left, right))
    _match, mismatch, errors = filecmp.cmpfiles(left, right, files_under(left), shallow=False)
    test.assertEqual(mismatch, [], "content differs: %s" % mismatch)
    test.assertEqual(errors, [], "could not compare: %s" % errors)


class NoSymlinksTest(unittest.TestCase):
    def test_no_symlink_anywhere_under_plugins(self):
        self.assertEqual(symlinks_under(PLUGINS), [])

    def test_each_plugin_has_a_real_skills_directory_with_skills_in_it(self):
        for name in sorted(os.listdir(PLUGINS)):
            plugin = os.path.join(PLUGINS, name)
            if not os.path.isdir(plugin):
                continue
            with self.subTest(plugin=name):
                skills = os.path.join(plugin, "skills")
                self.assertTrue(os.path.isdir(skills) and not os.path.islink(skills))
                skill_files = [d for d in os.listdir(skills)
                               if os.path.isfile(os.path.join(skills, d, "SKILL.md"))]
                self.assertGreater(len(skill_files), 0)


class SameBytesTest(unittest.TestCase):
    def test_claude_code_skills_and_the_plugin_skills_are_the_same_files(self):
        assert_same_tree(self, os.path.join(REPO_ROOT, "skills"),
                         os.path.join(PLUGINS, "ai-workflow", "skills"))

    def test_app_skills_and_the_app_plugin_skills_are_the_same_files(self):
        assert_same_tree(self, os.path.join(REPO_ROOT, "claude_app", "skills"),
                         os.path.join(PLUGINS, "ai-workflow-app", "skills"))

    def test_app_plugin_carries_the_same_scanner_as_the_claude_code_skill(self):
        assert_same_tree(self, os.path.join(REPO_ROOT, "skills", "style-audit", "scripts"),
                         os.path.join(PLUGINS, "ai-workflow-app", "skills", "style-audit", "scripts"))

    def test_app_plugin_carries_the_same_math_references(self):
        assert_same_tree(self, os.path.join(REPO_ROOT, "skills", "math", "references"),
                         os.path.join(PLUGINS, "ai-workflow-app", "skills", "math", "references"))

    def test_handoff_command_is_a_real_file_with_the_documented_text(self):
        inside = os.path.join(PLUGINS, "ai-workflow", "commands", "handoff.md")
        self.assertTrue(os.path.isfile(inside) and not os.path.islink(inside))
        with open(inside, encoding="ascii") as a, \
             open(os.path.join(REPO_ROOT, "handoff_command.md"), encoding="ascii") as b:
            self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
