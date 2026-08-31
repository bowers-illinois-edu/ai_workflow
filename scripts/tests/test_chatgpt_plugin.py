"""Tests for the ChatGPT package built from the Claude app skills.

The Claude and ChatGPT packages should share one copy of each skill. The two
apps may require different manifest files, but a writing rule or mathematical
protocol should never need to be updated twice. These tests therefore check
both the ChatGPT manifest and the shared skill directory.

The tests are stdlib-only and offline. They check the files that GitHub will
serve, not a cached copy installed on this machine.
"""

import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "ai-workflow-app"
SKILLS_ROOT = REPO_ROOT / "claude_app" / "skills"
PLUGIN_SKILLS = PLUGIN_ROOT / "skills"
CLAUDE_MANIFEST = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
CHATGPT_MANIFEST = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
EXPECTED_SKILLS = {
    "bowers-code",
    "bowers-prose",
    "handoff",
    "math",
    "style-audit",
}


def read_json(path):
    with path.open(encoding="ascii") as stream:
        return json.load(stream)


def frontmatter(text, path):
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if match is None:
        raise AssertionError(f"{path} has no YAML frontmatter")

    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def strings_in(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings_in(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings_in(item)


class NativeManifestTests(unittest.TestCase):
    def test_chatgpt_manifest_declares_the_shared_skills(self):
        self.assertTrue(
            CHATGPT_MANIFEST.is_file(),
            "The plugin needs .codex-plugin/plugin.json for ChatGPT.",
        )
        manifest = read_json(CHATGPT_MANIFEST)
        self.assertEqual(manifest.get("name"), PLUGIN_ROOT.name)
        self.assertRegex(manifest.get("version", ""), r"^\d+\.\d+\.\d+$")
        self.assertEqual(manifest.get("skills"), "./skills/")
        self.assertEqual(manifest.get("author", {}).get("name"), "Jake Bowers")

        interface = manifest.get("interface", {})
        for field in (
            "displayName",
            "shortDescription",
            "longDescription",
            "developerName",
            "category",
        ):
            self.assertTrue(interface.get(field), f"interface.{field} is required")

    def test_marketplace_and_both_manifests_name_the_same_plugin(self):
        marketplace = read_json(MARKETPLACE)
        entries = {
            entry["name"]: entry for entry in marketplace.get("plugins", [])
        }
        self.assertIn(PLUGIN_ROOT.name, entries)

        source = (REPO_ROOT / entries[PLUGIN_ROOT.name]["source"]).resolve()
        self.assertEqual(source, PLUGIN_ROOT.resolve())
        self.assertEqual(read_json(CLAUDE_MANIFEST)["name"], PLUGIN_ROOT.name)

        self.assertTrue(
            CHATGPT_MANIFEST.is_file(),
            "The marketplace source has no native ChatGPT manifest.",
        )
        self.assertEqual(read_json(CHATGPT_MANIFEST)["name"], PLUGIN_ROOT.name)


class SharedSkillTests(unittest.TestCase):
    def test_plugin_uses_the_existing_skill_directory(self):
        self.assertTrue(PLUGIN_SKILLS.is_symlink())
        self.assertEqual(PLUGIN_SKILLS.resolve(), SKILLS_ROOT.resolve())

    def test_each_skill_has_matching_frontmatter(self):
        skill_files = sorted(SKILLS_ROOT.glob("*/SKILL.md"))
        self.assertEqual({path.parent.name for path in skill_files}, EXPECTED_SKILLS)

        for path in skill_files:
            with self.subTest(skill=path.parent.name):
                fields = frontmatter(path.read_text(encoding="ascii"), path)
                self.assertEqual(fields.get("name"), path.parent.name)
                self.assertTrue(fields.get("description"))

    def test_every_symlink_in_the_shared_skills_resolves(self):
        broken = []
        for path in SKILLS_ROOT.rglob("*"):
            if path.is_symlink() and not path.exists():
                broken.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(broken, [])


class PortableLanguageTests(unittest.TestCase):
    def test_install_metadata_does_not_describe_one_assistant(self):
        marketplace = read_json(MARKETPLACE)
        values = list(strings_in({
            "description": marketplace.get("description", ""),
            "plugins": marketplace.get("plugins", []),
        }))
        values.extend(strings_in(read_json(CLAUDE_MANIFEST)))
        if CHATGPT_MANIFEST.is_file():
            values.extend(strings_in(read_json(CHATGPT_MANIFEST)))

        mentions = [value for value in values if re.search(r"\bClaude\b", value)]
        self.assertEqual(
            mentions,
            [],
            "Marketplace descriptions should explain the work, not name one assistant.",
        )

    def test_shared_skill_instructions_are_provider_neutral(self):
        mentions = []
        for path in sorted(SKILLS_ROOT.glob("*/SKILL.md")):
            text = path.read_text(encoding="ascii")
            text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
            for number, line in enumerate(text.splitlines(), start=1):
                if re.search(r"\bClaude\b", line):
                    mentions.append(f"{path.relative_to(REPO_ROOT)}:{number}: {line}")

        self.assertEqual(
            mentions,
            [],
            "Shared instructions should describe the capable agent, not one product.",
        )

    def test_plugin_text_files_are_ascii(self):
        paths = [MARKETPLACE, CLAUDE_MANIFEST]
        paths.extend(sorted(SKILLS_ROOT.glob("*/SKILL.md")))
        if CHATGPT_MANIFEST.is_file():
            paths.append(CHATGPT_MANIFEST)

        non_ascii = []
        for path in paths:
            try:
                path.read_text(encoding="ascii")
            except UnicodeDecodeError:
                non_ascii.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(non_ascii, [])


if __name__ == "__main__":
    unittest.main()
