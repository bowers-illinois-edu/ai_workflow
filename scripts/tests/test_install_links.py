"""Tests for scripts/install_links.py.

The substantive point of the install script is not "does it call ln." It is
that running it on a machine that already has hand-made links must be safe.
The ten links in ~/.claude/skills/ were made by hand over several months, two
of them point at a different repository entirely (.codegpt), and settings.json
sits in the same tree. So the tests below are mostly about what the script
must refuse to touch.

Stdlib only, offline, no network, matching the other suites in this repo.
"""

import json
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
        # the Codex side: a built AGENTS.md and the hooks template
        os.makedirs(os.path.join(self.repo, "codex"))
        with open(os.path.join(self.repo, "codex", "AGENTS.md"), "w") as fh:
            fh.write("# generated for codex\n")
        with open(os.path.join(self.repo, "codex", "hooks.json"), "w") as fh:
            fh.write('{"hooks": {"Stop": [{"hooks": [{"type": "command", '
                     '"command": "python3 __REPO__/skills/style-audit/scripts/style_gate.py stop"}]}]}}\n')
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

    def codex_target(self, *parts):
        p = os.path.join(self.home, ".codex", *parts)
        return os.readlink(p) if os.path.islink(p) else None

    def install_codex(self):
        """Codex is installed on this machine when ~/.codex exists."""
        os.makedirs(os.path.join(self.home, ".codex"), exist_ok=True)

    # --- what it must create -------------------------------------------

    def test_links_each_skill_directory(self):
        self.run_install()
        self.assertEqual(self.link_target("skills", "math"),
                         os.path.join(self.repo, "skills", "math"))
        self.assertEqual(self.link_target("skills", "decks"),
                         os.path.join(self.repo, "skills", "decks"))

    def test_skips_a_plugin_only_skill(self):
        """bowers-prose exists for a collaborator who installs the plugin and
        has no CLAUDE.md. Jake has CLAUDE.md, so a link would put the same
        rules in his context twice."""
        os.makedirs(os.path.join(self.repo, "skills", "bowers-prose"))
        self.run_install()
        self.assertFalse(os.path.lexists(os.path.join(self.home, ".claude", "skills", "bowers-prose")))
        self.assertTrue(os.path.islink(os.path.join(self.home, ".claude", "skills", "math")))

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


    # --- the Codex side ---------------------------------------------------
    #
    # Codex reads ~/.codex/AGENTS.md and ~/.codex/skills/<name>/, so the same
    # rules and skills reach it through the same kind of link. Two things
    # differ. The instruction file is the built codex/AGENTS.md, not
    # CLAUDE.md, because Codex follows no import lines. And the hooks that
    # run the style gate are written rather than linked, because a hook
    # command needs the repository's absolute path, and only on request,
    # because they change what every Codex session does.

    def test_touches_nothing_under_codex_when_codex_is_not_installed(self):
        self.run_install()
        self.assertFalse(os.path.exists(os.path.join(self.home, ".codex")))

    def test_links_the_built_agents_md_into_codex(self):
        self.install_codex()
        self.run_install()
        self.assertEqual(self.codex_target("AGENTS.md"),
                         os.path.join(self.repo, "codex", "AGENTS.md"))

    def test_links_each_skill_directory_into_codex(self):
        self.install_codex()
        self.run_install()
        self.assertEqual(self.codex_target("skills", "math"),
                         os.path.join(self.repo, "skills", "math"))
        self.assertEqual(self.codex_target("skills", "decks"),
                         os.path.join(self.repo, "skills", "decks"))

    def test_repoints_an_agents_md_link_that_went_to_claude_md(self):
        """How this laptop was wired on 2026-08-06: the link went straight to
        CLAUDE.md, whose two @ lines Codex cannot follow. The link is ours,
        so the installer moves it to the built file."""
        self.install_codex()
        link = os.path.join(self.home, ".codex", "AGENTS.md")
        os.symlink(os.path.join(self.repo, "CLAUDE.md"), link)
        self.run_install()
        self.assertEqual(os.readlink(link), os.path.join(self.repo, "codex", "AGENTS.md"))

    def test_skips_the_agents_md_link_when_the_build_is_missing(self):
        self.install_codex()
        os.remove(os.path.join(self.repo, "codex", "AGENTS.md"))
        r = self.run_install()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(os.path.lexists(os.path.join(self.home, ".codex", "AGENTS.md")),
                         "never link a file that does not exist")

    def test_refuses_to_replace_a_real_codex_skill_directory(self):
        """~/.codex/skills/ai-workflow-coding on this laptop is a real
        directory made by hand. Nothing in the plan has that name, but a
        real directory under a name the plan does use must survive."""
        self.install_codex()
        real = os.path.join(self.home, ".codex", "skills", "math")
        os.makedirs(real)
        with open(os.path.join(real, "SKILL.md"), "w") as fh:
            fh.write("someone's real work\n")
        r = self.run_install()
        self.assertTrue(os.path.isdir(real) and not os.path.islink(real))
        self.assertNotEqual(r.returncode, 0)

    def test_codex_hooks_are_not_written_unless_asked(self):
        self.install_codex()
        self.run_install()
        self.assertFalse(os.path.exists(os.path.join(self.home, ".codex", "hooks.json")))

    def test_codex_hooks_flag_writes_the_template_with_the_repo_path(self):
        self.install_codex()
        r = self.run_install("--codex-hooks")
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(self.home, ".codex", "hooks.json")) as fh:
            text = fh.read()
        self.assertNotIn("__REPO__", text)
        self.assertIn(os.path.join(self.repo, "skills", "style-audit", "scripts", "style_gate.py"), text)
        import json
        json.loads(text)

    def test_codex_hooks_flag_adds_the_gate_to_a_hooks_file_it_did_not_write(self):
        """Until 2026-11-09 the installer refused a hooks file that ran no
        gate, because writing the template over it would have deleted it.
        A merge deletes nothing, so Jake chose on 2026-11-09 to add the gate
        to such a file and keep what was there."""
        self.install_codex()
        theirs = os.path.join(self.home, ".codex", "hooks.json")
        with open(theirs, "w") as fh:
            fh.write('{"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "say done"}]}]}}\n')
        r = self.run_install("--codex-hooks")
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(theirs) as fh:
            merged = json.load(fh)
        self.assertEqual(commands(merged, "Stop"), ["say done", gate_command(self.repo, "stop")])

    def test_codex_hooks_flag_rewrites_a_file_it_wrote_before(self):
        self.install_codex()
        self.run_install("--codex-hooks")
        with open(os.path.join(self.repo, "codex", "hooks.json"), "a") as fh:
            pass
        r = self.run_install("--codex-hooks")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_dry_run_writes_no_codex_hooks(self):
        self.install_codex()
        self.run_install("--dry-run", "--codex-hooks")
        self.assertFalse(os.path.exists(os.path.join(self.home, ".codex", "hooks.json")))

    # --- merging into a hooks file other tools also write ------------------
    #
    # On 2026-11-09 ~/.codex/hooks.json held the two gate hooks and a third,
    # a SessionStart hook the Tuva plugin had added to print its usage
    # banner. Writing the template over the file would have deleted the Tuva
    # hook, so `make install` was not run. The installer now replaces only
    # its own hooks, the ones whose command runs style_gate.py, and keeps
    # every other hook where it was.

    def write_full_template(self):
        """The real template has a hook on two events; setUp's has one."""
        self.write_json(os.path.join(self.repo, "codex", "hooks.json"), {"hooks": {
            "UserPromptSubmit": [gate_group("__REPO__", "preflight")],
            "Stop": [gate_group("__REPO__", "stop")]}})

    def codex_hooks_path(self):
        return os.path.join(self.home, ".codex", "hooks.json")

    def write_json(self, path, obj):
        with open(path, "w") as fh:
            json.dump(obj, fh, indent=2)

    def read_json(self, path):
        with open(path) as fh:
            return json.load(fh)

    def test_codex_hooks_flag_keeps_a_hook_another_tool_added(self):
        self.install_codex()
        self.write_full_template()
        self.write_json(self.codex_hooks_path(), {"hooks": {
            "SessionStart": [TUVA_GROUP],
            "UserPromptSubmit": [gate_group(self.repo, "preflight")],
            "Stop": [gate_group(self.repo, "stop")]}})
        r = self.run_install("--codex-hooks")
        self.assertEqual(r.returncode, 0, r.stderr)
        merged = self.read_json(self.codex_hooks_path())
        self.assertIn("SessionStart", merged["hooks"], "the Tuva hook was deleted")
        self.assertEqual(merged["hooks"]["SessionStart"], [TUVA_GROUP],
                         "the Tuva hook must come through unchanged")
        self.assertEqual(commands(merged, "UserPromptSubmit"), [gate_command(self.repo, "preflight")])
        self.assertEqual(commands(merged, "Stop"), [gate_command(self.repo, "stop")])

    def test_codex_hooks_flag_replaces_its_own_hooks_rather_than_adding_copies(self):
        """A gate hook from an older clone of the repository, at another path,
        is ours, so it is replaced. Two gate hooks on Stop would run the gate
        twice after every reply."""
        self.install_codex()
        self.write_full_template()
        self.write_json(self.codex_hooks_path(), {"hooks": {
            "SessionStart": [TUVA_GROUP],
            "Stop": [gate_group("/old/clone", "stop")]}})
        self.run_install("--codex-hooks")
        merged = self.read_json(self.codex_hooks_path())
        self.assertEqual(commands(merged, "Stop"), [gate_command(self.repo, "stop")])
        self.assertNotIn("/old/clone", json.dumps(merged))
        for event, groups in merged["hooks"].items():
            for group in groups:
                self.assertTrue(group["hooks"],
                                "removing an old gate hook must not leave an empty group on %s" % event)

    def test_codex_hooks_flag_keeps_another_hook_on_the_same_event(self):
        """Another tool's Stop hook stays in its place, and the gate follows it."""
        self.install_codex()
        self.write_full_template()
        self.write_json(self.codex_hooks_path(), {"hooks": {
            "Stop": [SAY_DONE_GROUP, gate_group(self.repo, "stop")]}})
        self.run_install("--codex-hooks")
        merged = self.read_json(self.codex_hooks_path())
        self.assertEqual(commands(merged, "Stop"), ["say done", gate_command(self.repo, "stop")])

    def test_codex_hooks_merge_is_idempotent(self):
        self.install_codex()
        self.write_full_template()
        self.write_json(self.codex_hooks_path(), {"hooks": {
            "SessionStart": [TUVA_GROUP],
            "Stop": [SAY_DONE_GROUP, gate_group(self.repo, "stop")]}})
        self.run_install("--codex-hooks")
        with open(self.codex_hooks_path()) as fh:
            first = fh.read()
        r = self.run_install("--codex-hooks")
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(self.codex_hooks_path()) as fh:
            self.assertEqual(fh.read(), first)

    def test_codex_hooks_flag_refuses_a_hooks_file_that_is_not_json(self):
        """A file the installer cannot read is a file it cannot merge into
        without losing whatever is in it."""
        self.install_codex()
        broken = '{"hooks": {"Stop": [ style_gate.py\n'
        with open(self.codex_hooks_path(), "w") as fh:
            fh.write(broken)
        r = self.run_install("--codex-hooks")
        self.assertNotEqual(r.returncode, 0)
        with open(self.codex_hooks_path()) as fh:
            self.assertEqual(fh.read(), broken)

    def test_dry_run_leaves_an_existing_hooks_file_unchanged(self):
        self.install_codex()
        self.write_full_template()
        self.write_json(self.codex_hooks_path(), {"hooks": {
            "SessionStart": [TUVA_GROUP],
            "Stop": [gate_group("/old/clone", "stop")]}})
        with open(self.codex_hooks_path()) as fh:
            before = fh.read()
        r = self.run_install("--dry-run", "--codex-hooks")
        with open(self.codex_hooks_path()) as fh:
            self.assertEqual(fh.read(), before)
        self.assertIn("would merge", r.stdout.lower())


# The hook another tool added, copied in shape from ~/.codex/hooks.json on
# 2026-11-09 with the paths shortened.
TUVA_GROUP = {
    "hooks": [{
        "command": "/opt/tuva/python /opt/tuva/usage_banner.py --agent codex",
        "statusMessage": "Tuva: usage banner",
        "timeout": 10,
        "type": "command"}],
    "matcher": "startup"}

SAY_DONE_GROUP = {"hooks": [{"type": "command", "command": "say done"}]}


def gate_command(repo, mode):
    return "python3 %s/skills/style-audit/scripts/style_gate.py %s" % (repo, mode)


def gate_group(repo, mode):
    return {"hooks": [{"type": "command", "command": gate_command(repo, mode)}]}


def commands(hooks, event):
    """Every command on one event, in the order Codex would run them."""
    return [h["command"] for group in hooks["hooks"].get(event, []) for h in group["hooks"]]


if __name__ == "__main__":
    unittest.main()
