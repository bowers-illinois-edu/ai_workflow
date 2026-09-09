"""Every skill in skills/ must be findable, and its cross-references must resolve.

Two failures this suite exists to catch, both of which produce a skill that
works when you name it by hand and never loads on its own.

A skill that is not listed in CLAUDE.md is a skill no session knows about.
CLAUDE.md's `## Skills` list is what a session reads at startup; the directory
under skills/ is not read until something already decided to load it. On
2026-09-09 `both-passes` was written and the CLAUDE.md line was nearly
forgotten, which is what prompted these tests. README.md's manual install loop
is the same failure on a new machine: a name missing from that loop is a skill
that never gets its symlink.

A pointer from one skill to another goes stale when a skill is renamed or
removed. `both-passes` exists only to order `style-audit` and `first-reader`,
and each of those two points back at it, because a session that loads one pass
alone has to hear that the order matters before it starts editing. Four
references, none of them checked by anything else in the repository.

The frontmatter checks come along because a `name:` that disagrees with its
directory is the same class of fault: the Skill tool takes the directory name
and the description takes the frontmatter, so a mismatch splits one skill into
two half-registered ones.

Stdlib only, offline.
"""

import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILLS = os.path.join(REPO_ROOT, "skills")
CLAUDE_MD = os.path.join(REPO_ROOT, "CLAUDE.md")
README = os.path.join(REPO_ROOT, "README.md")

# Source skill -> the skills its SKILL.md must name. Adding a pair is one line.
# Each entry is a pointer somebody has to follow: without it, a session running
# the named pass alone never learns the other exists.
REQUIRED_REFERENCES = {
    "both-passes": ("style-audit", "first-reader"),
    "style-audit": ("first-reader", "both-passes"),
    "first-reader": ("style-audit", "both-passes"),
}


def skill_names():
    """Directory names under skills/, which is what the Skill tool matches on."""
    return sorted(name for name in os.listdir(SKILLS)
                  if os.path.isfile(os.path.join(SKILLS, name, "SKILL.md")))


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def frontmatter_field(text, field):
    """The value of one YAML field in the leading --- block, or None.

    Hand-rolled rather than imported: PyYAML is not a dependency here, and the
    frontmatter these files carry is two flat string fields.
    """
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    for line in text[4:end].split("\n"):
        match = re.match(r"^%s:\s*(.+)$" % re.escape(field), line)
        if match:
            return match.group(1).strip()
    return None


class FrontmatterTest(unittest.TestCase):
    def test_every_skill_has_a_skill_md_with_name_and_description(self):
        names = skill_names()
        self.assertGreater(len(names), 0, "no skills found under skills/")
        for name in names:
            with self.subTest(skill=name):
                text = read(os.path.join(SKILLS, name, "SKILL.md"))
                self.assertEqual(frontmatter_field(text, "name"), name,
                                 "frontmatter name must equal the directory name")
                description = frontmatter_field(text, "description")
                self.assertTrue(description, "a skill with no description never triggers")


class DiscoveryTest(unittest.TestCase):
    def test_claude_md_lists_every_skill(self):
        """The startup list. A skill missing here loads only when named by hand."""
        text = read(CLAUDE_MD)
        listed = set(re.findall(r"^- `([a-z0-9-]+)`", text, re.MULTILINE))
        for name in skill_names():
            with self.subTest(skill=name):
                self.assertIn(name, listed,
                              "add a `- `%s` --- ...` line to the Skills list" % name)

    def test_readme_install_loop_names_every_skill(self):
        """The hand-install path on a new machine, README's `for s in ...` loop."""
        text = read(README)
        loops = re.findall(r"^for s in ([a-z0-9 -]+); do", text, re.MULTILINE)
        self.assertEqual(len(loops), 1, "expected exactly one skill install loop")
        in_loop = set(loops[0].split())
        for name in skill_names():
            with self.subTest(skill=name):
                self.assertIn(name, in_loop)


class CrossReferenceTest(unittest.TestCase):
    def test_named_skills_exist(self):
        """A pointer table entry naming a skill that is gone is itself the bug."""
        existing = set(skill_names())
        for source, targets in REQUIRED_REFERENCES.items():
            with self.subTest(skill=source):
                self.assertIn(source, existing)
                for target in targets:
                    self.assertIn(target, existing)

    def test_each_skill_points_at_the_skills_it_depends_on(self):
        for source, targets in REQUIRED_REFERENCES.items():
            text = read(os.path.join(SKILLS, source, "SKILL.md"))
            for target in targets:
                with self.subTest(skill=source, points_to=target):
                    self.assertIn(target, text,
                                  "%s must name %s" % (source, target))


if __name__ == "__main__":
    unittest.main()
