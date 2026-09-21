"""The Claude Code plugin gives a collaborator the coding and writing rules.

Someone who installs `ai-workflow` from this repository's marketplace gets the
nine skills and nothing that loads on its own. Jake's rules for code and for
prose reach him only through `@` imports in his own ~/.claude/CLAUDE.md, and a
plugin cannot ship a CLAUDE.md. What a plugin can ship is a SessionStart hook,
whose standard output enters the session's context once at startup and again
after a compaction, and Claude Code caps that output at 10,000 characters.
CLAUDE_CODING.md fits under the cap and the writing rules do not, so the two
travel differently. The coding rules go as a hook: plugins/ai-workflow/hooks/hooks.json
prints plugins/ai-workflow/rules/coding.md, a copy of CLAUDE_CODING.md. The
writing rules go as a skill: a copy of the app plugin's bowers-prose, whose
body was already written for a reader who is not on Jake's machine, with a
description aimed at documents rather than at chat, because Jake said on
2026-09-20 that a collaborator may have Claude talk to them however they like
and what he needs from them is the code, the citations, the math, and the
prose of memos and papers.

Three things have to stay true. The copies must match their sources, or the
collaborator reads rules Jake no longer holds; scripts/build_plugin_rules.py
refreshes the coding copy and `make plugins` runs it; the test runs it into a
temporary directory so that a test never rewrites a tracked file. The hook, run the way
Claude Code runs it, with CLAUDE_PLUGIN_ROOT set to the plugin directory, must
print the coding rules in plain ASCII and under the cap. And the prose skill's
body must be the app skill's body byte for byte.

Stdlib only, offline.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLUGIN = os.path.join(REPO_ROOT, "plugins", "ai-workflow")
HOOKS = os.path.join(PLUGIN, "hooks", "hooks.json")
RULES = os.path.join(PLUGIN, "rules")
CODING_SOURCE = os.path.join(REPO_ROOT, "CLAUDE_CODING.md")
PROSE_SOURCE = os.path.join(REPO_ROOT, "plugins", "ai-workflow-app", "skills",
                            "bowers-prose", "SKILL.md")
PROSE_COPY = os.path.join(PLUGIN, "skills", "bowers-prose", "SKILL.md")
BUILDER = os.path.join(REPO_ROOT, "scripts", "build_plugin_rules.py")
STDOUT_CAP = 10000


def read(path):
    with open(path, encoding="ascii") as fh:
        return fh.read()


def split_frontmatter(text):
    """(frontmatter lines, body) for a SKILL.md.

    Kept here rather than imported from the builder so that the test states
    the expectation independently of the code it checks.
    """
    assert text.startswith("---\n")
    end = text.index("\n---\n", 4)
    return text[4:end].split("\n"), text[end + len("\n---\n"):]


def session_start_commands():
    with open(HOOKS, encoding="ascii") as fh:
        hooks = json.load(fh)
    return [h["command"]
            for group in hooks["hooks"]["SessionStart"]
            for h in group["hooks"]
            if h.get("type") == "command"]


def run_hook(command):
    """Run the hook the way Claude Code does: a shell, with the plugin root set."""
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=PLUGIN)
    return subprocess.run(command, shell=True, env=env, capture_output=True,
                          text=True, check=True, input="{}").stdout


class HookShapeTest(unittest.TestCase):
    def test_plugin_declares_one_session_start_command_hook(self):
        self.assertEqual(len(session_start_commands()), 1)

    def test_hook_finds_its_file_through_the_plugin_root_variable(self):
        """Installed plugins live under ~/.claude/plugins/..., never at a path
        this repository can know, so the command must resolve its file through
        CLAUDE_PLUGIN_ROOT and nothing else."""
        command = session_start_commands()[0]
        self.assertIn("${CLAUDE_PLUGIN_ROOT}", command)
        self.assertNotIn(REPO_ROOT, command)
        self.assertNotIn("~", command)


class CopiesMatchSourcesTest(unittest.TestCase):
    def test_coding_rules_are_claude_coding_md_verbatim(self):
        self.assertEqual(read(os.path.join(RULES, "coding.md")), read(CODING_SOURCE))

    def test_builder_writes_the_same_copy_the_tree_holds(self):
        """Run into a temporary directory, never the tracked one: a test that
        rewrote rules/ would hide the drift the verbatim test exists to show."""
        out = tempfile.mkdtemp()
        try:
            subprocess.run(["python3", BUILDER, out], check=True, capture_output=True)
            self.assertEqual(sorted(os.listdir(out)), sorted(os.listdir(RULES)))
            self.assertEqual(read(os.path.join(out, "coding.md")), read(CODING_SOURCE))
        finally:
            shutil.rmtree(out)


class ProseSkillTest(unittest.TestCase):
    def test_prose_skill_body_is_the_app_skill_body(self):
        _, source_body = split_frontmatter(read(PROSE_SOURCE))
        _, copy_body = split_frontmatter(read(PROSE_COPY))
        self.assertEqual(copy_body, source_body)

    def test_prose_skill_is_named_and_described_for_documents(self):
        """The app version says to use it for every reply to Jake. The
        collaborator's version triggers on documents and leaves chat alone."""
        front, _ = split_frontmatter(read(PROSE_COPY))
        fields = dict(line.split(":", 1) for line in front if ":" in line)
        self.assertEqual(fields["name"].strip(), "bowers-prose")
        description = fields["description"].lower()
        for word in ("paper", "memo"):
            self.assertIn(word, description)
        self.assertNotIn("every reply", description)


class WhatTheCollaboratorReceivesTest(unittest.TestCase):
    """The point of the arrangement: run the hook and read what comes out."""

    def setUp(self):
        self.output = run_hook(session_start_commands()[0])

    def test_output_carries_the_tests_first_rule(self):
        # The rule that two skill scripts once shipped without; if any one
        # sentence has to reach a collaborator, it is this one.
        self.assertIn("Write well commented unit tests **before** writing code", self.output)

    def test_output_carries_the_review_checkpoints(self):
        self.assertIn("After writing tests and before writing implementation", self.output)

    def test_output_is_under_the_cap_claude_code_applies(self):
        """Past 10,000 characters Claude Code truncates, and a truncated rules
        file ends mid-sentence with no sign that anything is missing."""
        self.assertLess(len(self.output), STDOUT_CAP)

    def test_output_is_printable_ascii(self):
        bad = sorted({c for c in self.output if not (32 <= ord(c) <= 126 or c in "\n\t")})
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
