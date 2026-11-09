#!/usr/bin/env python3
"""Symlink this repository's rules and skills into ~/.claude and ~/.codex.

Cloning the repository onto a new machine leaves Claude Code and Codex unable
to see any of it: each reads its own directory under the home directory, and
the repository is somewhere else. Until 2026-08-31 the connection was ten
symlinks made by hand over several months, which is not something anyone
would reconstruct correctly from memory on a new laptop. This script makes
them, and `make install` calls it.

Into ~/.claude, matching how the tree was wired by hand:

    CLAUDE.md            -> ~/.claude/CLAUDE.md
    skills/<name>/       -> ~/.claude/skills/<name>
    output-styles/*.md   -> ~/.claude/output-styles/*.md
    agents/*.md          -> ~/.claude/agents/*.md      (if agents/ exists)

Into ~/.codex, only when that directory already exists, because its existence
is what says Codex is installed on the machine:

    codex/AGENTS.md      -> ~/.codex/AGENTS.md
    skills/<name>/       -> ~/.codex/skills/<name>

Codex gets the built codex/AGENTS.md rather than CLAUDE.md because it follows
no import lines; scripts/build_agents_md.py writes the two imported files out
in place. With --codex-hooks the script also fills this repository's
absolute path into the template codex/hooks.json and merges the result into
~/.codex/hooks.json, so the style gate runs in Codex as it runs in Claude
Code. That is a write rather than a link because a hook command needs
the absolute path. It is a merge rather than a copy because other tools add
their own hooks to the same file: the gate hooks are replaced and every other
hook is kept. A hooks file that is not valid JSON is refused.

The care in here is all about not destroying things. Two of the skills in
~/.claude/skills point at a different repository (~/.codegpt), a hand-made
skill directory sits in ~/.codex/skills, and a settings file the script has no
business touching sits one directory up. So a link pointing outside this
repository is left alone and reported, and anything that is a real file or
directory rather than a symlink stops the run.
"""

import argparse
import json
import os
import sys

HOOKS_TEMPLATE = os.path.join("codex", "hooks.json")
# A hook whose command runs the gate is one this script wrote, or one Jake
# wrote to the same end; either way it is ours to replace. Every other hook
# in the file belongs to someone else and is kept.
HOOKS_MARKER = "style_gate.py"

# Skills that exist for a collaborator who installs the plugin and has no
# CLAUDE.md. On this machine their content is already in context through
# CLAUDE.md's imports, so linking them would load the same rules twice.
# test_skill_registry.py reads this set to keep them out of CLAUDE.md's
# skills list and the README install loop.
PLUGIN_ONLY_SKILLS = frozenset({"bowers-prose"})


def skill_dirs(repo):
    """(absolute source, name) for each skill directory.

    `skills/` is a symlink into plugins/ai-workflow/ since 2026-09-02; listing
    it follows the link, and the sources keep the `skills/<name>` spelling so
    the links already on this machine read as correct rather than stale.
    """
    skills = os.path.join(repo, "skills")
    if not os.path.isdir(skills):
        return []
    # the .zip files beside the skills are packaging for the Claude app,
    # built by `make app-skills`; Claude Code and Codex want the directory
    return [(os.path.join(skills, name), name)
            for name in sorted(os.listdir(skills))
            if os.path.isdir(os.path.join(skills, name))
            and name not in PLUGIN_ONLY_SKILLS]


def plan(repo):
    """Return [(source, destination-relative-to-.claude)] for every link.

    Sources are absolute so the symlinks survive the working directory
    changing, which is how the existing hand-made links are written.
    """
    items = []

    claude_md = os.path.join(repo, "CLAUDE.md")
    if os.path.isfile(claude_md):
        items.append((claude_md, "CLAUDE.md"))

    for src, name in skill_dirs(repo):
        items.append((src, os.path.join("skills", name)))

    styles = os.path.join(repo, "output-styles")
    if os.path.isdir(styles):
        for name in sorted(os.listdir(styles)):
            if name.endswith(".md"):
                items.append((os.path.join(styles, name),
                              os.path.join("output-styles", name)))

    # agents/ does not exist yet. It is where a first-reader agent definition
    # would live if the speed study concludes the pass should run at a
    # different model or effort, because frontmatter travels with the clone
    # and a settings.json edit does not.
    agents = os.path.join(repo, "agents")
    if os.path.isdir(agents):
        for name in sorted(os.listdir(agents)):
            if name.endswith(".md"):
                items.append((os.path.join(agents, name),
                              os.path.join("agents", name)))

    return items


def codex_plan(repo):
    """Return [(source, destination-relative-to-.codex)] for every link."""
    items = []
    agents_md = os.path.join(repo, "codex", "AGENTS.md")
    if os.path.isfile(agents_md):
        items.append((agents_md, "AGENTS.md"))
    for src, name in skill_dirs(repo):
        items.append((src, os.path.join("skills", name)))
    return items


def link_all(items, root, repo, dry_run=False):
    """Make every link in `items` under `root`. Returns the number of refusals."""
    made = relinked = skipped = kept = refused = 0

    for src, rel in items:
        dst = os.path.join(root, rel)

        if os.path.islink(dst):
            current = os.readlink(dst)
            if current == src:
                print(f"  ok       {rel}")
                kept += 1
                continue
            if not current.startswith(repo + os.sep):
                # someone else's link, and not ours to move
                print(f"  skipped  {rel} -> {current} (points outside {repo})")
                skipped += 1
                continue
            if dry_run:
                print(f"  would relink {rel} (was {current})")
            else:
                os.unlink(dst)
                os.symlink(src, dst)
                print(f"  relinked {rel} (was {current})")
            relinked += 1
            continue

        if os.path.lexists(dst):
            # a real file or directory: refuse, and say so loudly
            print(f"  REFUSED  {rel} exists and is not a symlink", file=sys.stderr)
            refused += 1
            continue

        if dry_run:
            print(f"  would link {rel} -> {src}")
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.symlink(src, dst)
            print(f"  linked   {rel}")
        made += 1

    print(f"  {made} to make, {relinked} to repair, {kept} already correct, "
          f"{skipped} skipped, {refused} refused")
    return refused


def is_gate_hook(hook):
    return HOOKS_MARKER in hook.get("command", "")


def merge_hooks(existing, template):
    """Return `existing` with its gate hooks replaced by the template's.

    Every other hook keeps its group and its place. A group that held only
    gate hooks is dropped rather than left empty, and the template's groups
    go at the end of their event, after any other tool's hooks there.
    """
    events = {}
    for event, groups in existing.get("hooks", {}).items():
        kept = []
        for group in groups:
            hooks = group.get("hooks", [])
            others = [h for h in hooks if not is_gate_hook(h)]
            if len(others) == len(hooks):
                kept.append(group)
            elif others:
                kept.append(dict(group, hooks=others))
        # an event emptied by removing the gate goes; one somebody left
        # empty on purpose stays
        if kept or not groups:
            events[event] = kept
    for event, groups in template["hooks"].items():
        events.setdefault(event, []).extend(groups)
    return dict(existing, hooks=events)


def write_codex_hooks(repo, codex_root, dry_run=False):
    """Merge the template's gate hooks into ~/.codex/hooks.json.

    Returns refusals (0 or 1). Other tools write hooks into the same file.
    On 2026-11-09 it held a SessionStart hook from the Tuva plugin. So the
    file is read, only the gate hooks are replaced, and everything else is
    written back with its content unchanged.
    """
    template = os.path.join(repo, HOOKS_TEMPLATE)
    dst = os.path.join(codex_root, "hooks.json")
    with open(template, encoding="ascii") as fh:
        ours = json.loads(fh.read().replace("__REPO__", repo))

    existing = {"hooks": {}}
    if os.path.exists(dst):
        try:
            with open(dst, encoding="utf-8") as fh:
                existing = json.load(fh)
            merged = merge_hooks(existing, ours)
        except (ValueError, AttributeError, TypeError) as err:
            # a file we cannot read is a file we cannot merge into without
            # losing whatever is in it
            print(f"  REFUSED  hooks.json is not a hooks file this script can "
                  f"read ({err}); merge {HOOKS_TEMPLATE} into it by hand",
                  file=sys.stderr)
            return 1
        if merged == existing:
            print("  ok       hooks.json")
            return 0
        verb = "would merge into" if dry_run else "merged into"
    else:
        merged = merge_hooks(existing, ours)
        verb = "would write" if dry_run else "wrote"

    others = sum(1 for groups in merged["hooks"].values()
                 for group in groups for h in group.get("hooks", [])
                 if not is_gate_hook(h))
    if not dry_run:
        with open(dst, "w", encoding="ascii") as fh:
            fh.write(json.dumps(merged, indent=2) + "\n")
    print(f"  {verb} hooks.json (hooks from other tools kept: {others})")
    return 0


def install(repo, home, dry_run=False, codex_hooks=False):
    """Link into ~/.claude, and into ~/.codex when it exists. Returns refusals."""
    print(f"~/.claude:")
    refused = link_all(plan(repo), os.path.join(home, ".claude"), repo, dry_run)

    codex_root = os.path.join(home, ".codex")
    if os.path.isdir(codex_root):
        print(f"\n~/.codex:")
        refused += link_all(codex_plan(repo), codex_root, repo, dry_run)
        if codex_hooks:
            refused += write_codex_hooks(repo, codex_root, dry_run)
    else:
        print(f"\n~/.codex: not present, so Codex is not installed here; nothing to do")

    if refused:
        print("\nRefused entries are real files or directories. Move or delete "
              "them by hand, then run this again.", file=sys.stderr)
    return refused


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    ap.add_argument("--home", default=os.path.expanduser("~"))
    ap.add_argument("--dry-run", action="store_true",
                    help="say what would happen and change nothing")
    ap.add_argument("--codex-hooks", action="store_true",
                    help="also write ~/.codex/hooks.json so the style gate runs in Codex")
    args = ap.parse_args()

    print(f"repository: {args.repo}\n")
    sys.exit(1 if install(args.repo, args.home, args.dry_run, args.codex_hooks) else 0)


if __name__ == "__main__":
    main()
