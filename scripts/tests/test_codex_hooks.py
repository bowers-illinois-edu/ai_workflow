"""codex/hooks.json wires the style gate into Codex.

Codex hooks use the envelope Claude Code's use: a UserPromptSubmit hook
returns additionalContext, and a Stop hook receives last_assistant_message.
style_gate.py already reads exactly those fields, so the same two commands
serve both tools. The file in the repository is a template with __REPO__
where the repository path goes, because a hook command needs an absolute
path and the repository lives somewhere different on every machine.
install_links.py --codex-hooks fills it in; those tests live beside the
installer's.

Stdlib only, offline.
"""

import json
import os
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE = os.path.join(REPO_ROOT, "codex", "hooks.json")


def load(repo="/x/y"):
    with open(TEMPLATE, encoding="ascii") as fh:
        return json.loads(fh.read().replace("__REPO__", repo))


def command(hooks, event):
    return hooks["hooks"][event][0]["hooks"][0]["command"]


class CodexHooksTemplateTest(unittest.TestCase):
    def test_template_is_json_once_the_path_is_filled(self):
        self.assertIn("hooks", load())

    def test_preflight_runs_before_each_prompt_and_stop_after_each_reply(self):
        hooks = load("/x/y")
        self.assertTrue(command(hooks, "UserPromptSubmit").endswith(
            "/x/y/skills/style-audit/scripts/style_gate.py preflight"))
        self.assertTrue(command(hooks, "Stop").endswith(
            "/x/y/skills/style-audit/scripts/style_gate.py stop"))

    def test_each_hook_is_a_command_hook(self):
        hooks = load()
        for event in ("UserPromptSubmit", "Stop"):
            self.assertEqual(hooks["hooks"][event][0]["hooks"][0]["type"], "command")

    def test_template_names_no_home_directory(self):
        with open(TEMPLATE, encoding="ascii") as fh:
            text = fh.read()
        self.assertNotIn("/Users/", text)
        self.assertIn("__REPO__", text)


if __name__ == "__main__":
    unittest.main()
