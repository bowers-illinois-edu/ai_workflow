#!/usr/bin/env python3
"""Report when a claude_app block is older than the file it was copied from.

The four blocks in `claude_app/` are pasted into the Claude app by hand, because
the app cannot read a file on this machine. That makes them copies of rules
whose canonical statement lives in `CLAUDE.md` and `CLAUDE_CODING.md`, and a
copy can drift. No program can tell whether a block still agrees with its
source, because the blocks are translations rather than transcriptions: first
person, cut to fit the app's field limits, reordered. What a program can tell is
whether the source has changed since the block was last synced, which is the
signal that a human re-read is owed.

Each block records its last sync in a line above the rule of dashes, so the
record never travels into the pasted text:

    Synced against CLAUDE.md at commit 55ed9ea (2026-08-23).

Exit status is 0 when every block is current, 1 when any block is stale or
carries no stamp, so `make check-claude-app` fails loudly rather than passing
in silence.
"""

import collections
import os
import re
import subprocess
import sys

Stamp = collections.namedtuple("Stamp", ["source", "sha"])

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCK_DIR = os.path.join(REPO_ROOT, "claude_app")

# The header ends at the first line of dashes. Everything after it is the text
# that gets pasted into the app, so a stamp found there is not the block's own
# record and must be ignored.
RULE_LINE = re.compile(r"^-{20,}\s*$", re.MULTILINE)

STAMP_LINE = re.compile(r"Synced against\s+(\S+\.md)\s+at commit\s+([0-9a-f]{7,40})")


def parse_stamps(text):
    """Return every Stamp recorded in a block's header, in the order written.

    A block can translate more than one source. `CLAUDE.md` imports
    `CLAUDE_WRITING_STANCE.md`, which the app cannot follow, so the two writing
    blocks copy rules from both files by hand. Reading only the first stamp
    would leave whichever source it did not name free to move in silence.
    """
    rule = RULE_LINE.search(text)
    header = text[: rule.start()] if rule else text
    return [Stamp(source=source, sha=sha)
            for source, sha in STAMP_LINE.findall(header)]


def physical_path(source, repo_root=REPO_ROOT):
    """The path git records changes at for `source`, with symlinks resolved.

    `skills/` is a symlink to `plugins/ai-workflow/skills/` since 2026-09-02,
    so a stamp that names `skills/math/SKILL.md` has to be looked up under the
    plugin path, or the log comes back empty and the block reads as current
    forever.
    """
    real_root = os.path.realpath(repo_root)
    real = os.path.realpath(os.path.join(repo_root, source))
    return os.path.relpath(real, real_root)


def git_commits_since(source, sha, repo_root=REPO_ROOT):
    """One-line log of commits touching `source` after `sha`, newest first."""
    result = subprocess.run(
        ["git", "log", "--oneline", "%s..HEAD" % sha, "--",
         physical_path(source, repo_root)],
        cwd=repo_root, capture_output=True, text=True,
    )
    if result.returncode != 0:
        # An unknown commit is itself a defect in the stamp, so say which stamp
        # rather than letting an empty log read as "nothing changed".
        raise ValueError(
            "git could not read the stamp %s for %s: %s"
            % (sha, source, result.stderr.strip())
        )
    return [line for line in result.stdout.splitlines() if line.strip()]


def find_stale(blocks, log):
    """Given (path, Stamp) pairs, return those whose source has moved.

    `log` is passed in rather than called directly so the tests can run offline,
    and it is asked about each block's own source: block 4 is synced against
    CLAUDE_CODING.md, and checking it against CLAUDE.md would let it rot.
    """
    stale = []
    for path, stamp in blocks:
        commits = log(stamp.source, stamp.sha)
        if commits:
            stale.append((path, stamp, commits))
    return stale


def format_report(stale, missing):
    """Human-readable report. Names the fix, because the fix is a hand edit."""
    if not stale and not missing:
        return "claude_app: every block is current with its source."

    lines = []
    for path, stamp, commits in stale:
        lines.append("%s is behind %s (stamped %s):" % (path, stamp.source, stamp.sha))
        for commit in commits:
            lines.append("    %s" % commit)
        newest = commits[0].split()[0]
        lines.append("    -> re-read the block, then stamp it %s" % newest)
        lines.append("")
    for path in missing:
        lines.append("%s carries no sync stamp; add one above the rule line." % path)
    return "\n".join(lines).rstrip()


def _default_paths():
    """Every app destination: the pasted blocks, then the uploaded skills.

    A skill drifts from its source the same way a pasted block does, so both
    kinds carry a stamp and both are checked. The skills keep theirs in an HTML
    comment, which keeps the record out of what Claude reads as instructions.
    """
    paths = [
        os.path.join("claude_app", name)
        for name in sorted(os.listdir(BLOCK_DIR))
        if name.endswith(".md")
    ]
    skills_dir = os.path.join(BLOCK_DIR, "skills")
    if os.path.isdir(skills_dir):
        for name in sorted(os.listdir(skills_dir)):
            skill = os.path.join(skills_dir, name, "SKILL.md")
            if os.path.exists(skill):
                paths.append(os.path.relpath(skill, REPO_ROOT))
    return paths


def _read(path):
    with open(os.path.join(REPO_ROOT, path)) as handle:
        return handle.read()


def main(paths=None, commits_for=None, out=None, read=None):
    paths = _default_paths() if paths is None else paths
    commits_for = git_commits_since if commits_for is None else commits_for
    out = print if out is None else out
    read = _read if read is None else read

    # One entry per (block, source) pair, so a block translating two sources is
    # checked against each and reported once for each that has moved.
    blocks, missing = [], []
    for path in paths:
        stamps = parse_stamps(read(path))
        if not stamps:
            missing.append(path)
        blocks.extend((path, stamp) for stamp in stamps)

    stale = find_stale(blocks, commits_for)
    out(format_report(stale, missing))
    return 1 if (stale or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
