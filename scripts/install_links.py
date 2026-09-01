#!/usr/bin/env python3
"""Symlink this repository's skills, rules, and agents into ~/.claude.

Cloning the repository onto a new machine leaves Claude Code unable to see any
of it: Claude Code reads ~/.claude, and the repository is somewhere else. Until
now the connection was ten symlinks made by hand over several months, which is
not something anyone would reconstruct correctly from memory on a new laptop.
This script makes them, and `make install` calls it.

Four kinds of link, matching how the tree is already wired on this machine:

    CLAUDE.md            -> ~/.claude/CLAUDE.md
    skills/<name>/       -> ~/.claude/skills/<name>
    output-styles/*.md   -> ~/.claude/output-styles/*.md
    agents/*.md          -> ~/.claude/agents/*.md      (if agents/ exists)

The care in here is all about not destroying things. Two of the skills in
~/.claude/skills point at a different repository (~/.codegpt), and a settings
file the script has no business touching sits one directory up. So a link
pointing outside this repository is left alone and reported, and anything that
is a real file or directory rather than a symlink stops the run.
"""

import argparse
import os
import sys


def plan(repo):
    """Return [(source, destination-relative-to-.claude)] for every link.

    Sources are absolute so the symlinks survive the working directory
    changing, which is how the existing hand-made links are written.
    """
    items = []

    claude_md = os.path.join(repo, "CLAUDE.md")
    if os.path.isfile(claude_md):
        items.append((claude_md, "CLAUDE.md"))

    skills = os.path.join(repo, "skills")
    if os.path.isdir(skills):
        for name in sorted(os.listdir(skills)):
            src = os.path.join(skills, name)
            # the .zip files beside the skills are packaging for the Claude
            # app, built by `make app-skills`; Claude Code wants the directory
            if os.path.isdir(src):
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


def install(repo, home, dry_run=False):
    """Make every link in the plan. Returns the number of refusals."""
    root = os.path.join(home, ".claude")
    made = relinked = skipped = kept = refused = 0

    for src, rel in plan(repo):
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

    print(f"\n{made} to make, {relinked} to repair, {kept} already correct, "
          f"{skipped} skipped, {refused} refused")
    if refused:
        print("Refused entries are real files or directories. Move or delete "
              "them by hand, then run this again.", file=sys.stderr)
    return refused


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    ap.add_argument("--home", default=os.path.expanduser("~"))
    ap.add_argument("--dry-run", action="store_true",
                    help="say what would happen and change nothing")
    args = ap.parse_args()

    print(f"repository: {args.repo}")
    print(f"target:     {os.path.join(args.home, '.claude')}\n")
    sys.exit(1 if install(args.repo, args.home, args.dry_run) else 0)


if __name__ == "__main__":
    main()
