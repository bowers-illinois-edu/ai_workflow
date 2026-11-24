#!/usr/bin/env python3
"""List active research projects, closest to completion first.

Jake's rule for a research morning is to work on whatever is closest to
completion, given the kind of work he is in the mood for. Applying the rule
needs, for every active project, an estimate of how much is left and the next
concrete step. Each project's HANDOFF.md already ends a session with a next
step, so this script reads a short header at the top of that file:

    ---
    next: rerun the size simulation and update Table 2
    kind: code
    milestone: draft to coauthors
    sessions_to_milestone: 3
    waiting_for:
    deadline: 2026-12-15
    ---

and prints one tab-separated row per project, fewest sessions first. The
`today` skill reads the table and offers at most three options.

Decisions behind the rules below (2026-10-25):

- A project is any immediate subdirectory of --root (default ~/repos) holding
  HANDOFF.md, matched without regard to case. Only `active: no` removes one;
  there is no time cutoff, because Jake returns to projects after a year.
- Jake keeps related projects together in folders such as ~/repos/EGAP. When
  an immediate subdirectory has neither .git nor HANDOFF.md, the script looks
  one level inside it and names what it finds EGAP/methodsweb (2026-11-24). A
  git repository, or a folder with its own HANDOFF.md, is one project and is
  never searched, so the script does not crawl renv/ or node_modules/.
- Ties on sessions go to the most recent commit, because he will remember
  more of it, and then to the repository name, so the order never depends on
  how a file system happens to list directories.
- What a project is waiting for is shown and never removes or reorders it,
  because Jake can always do something on a waiting project (2026-11-24).
- A deadline shows as days remaining and never changes the order. A passed
  deadline prints as blank and its date is not printed at all: an overdue
  count is what made Todoist and GitHub Issues into lists he stopped opening,
  and an agent shown the raw date would compute the count itself.
- STALE marks a header written on an earlier calendar day than the last
  commit. Sessions usually write HANDOFF.md minutes before committing, so a
  same-day header is current.
- Errors are errors. A missing --root exits nonzero instead of printing an
  empty table, which an agent would report as "you have no projects."
- The nightly archive job writes corpus_check.txt beside the transcript
  corpus, one line per month in which the corpus holds fewer of Jake's turns
  than the archive or Claude Code's folder. Jake chose on 2026-11-19 to hear
  about such a month here as well as by a Mac notification. The warning goes
  to stderr so the table an agent reads is unchanged, and a machine with no
  such file, such as a collaborator's, gets no warning.

Usage: python3 today.py [--root DIR] [--today YYYY-MM-DD] [--corpus-check FILE]
"""

import argparse
import datetime
import os
import re
import subprocess
import sys

COLUMNS = ["repo", "sessions_left", "days_since_commit", "deadline_in_days",
           "kind", "stale", "next", "waiting_for"]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_date(text):
    """A date written exactly YYYY-MM-DD, or None. Python 3.11 accepts other
    ISO forms in fromisoformat and 3.9 does not, so check the form first."""
    if not DATE_RE.match(text or ""):
        return None
    try:
        return datetime.datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def read_header(path):
    """The key: value lines between a leading '---' and the next '---', or
    None when the file has no complete header. Bytes that are not UTF-8 are
    kept as backslash escapes so one odd file cannot stop the run or break
    printing."""
    with open(path, "rb") as fh:
        text = fh.read().decode("utf-8", errors="backslashreplace")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        # Strip one pair of surrounding quotes, which YAML habits add.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        fields[key.strip().lower()] = value
    return None  # no closing line: treat as no header rather than guess


def handoff_in(folder):
    """The HANDOFF.md in this folder, matched without regard to case so the
    Mac (which ignores case) and Linux (which does not) agree."""
    try:
        names = os.listdir(folder)
    except OSError:
        return None
    if "HANDOFF.md" in names:
        return os.path.join(folder, "HANDOFF.md")
    for name in sorted(names):
        if name.lower() == "handoff.md":
            return os.path.join(folder, name)
    return None


def subfolders(folder):
    """Names of the visible folders directly inside this one, in order."""
    return [name for name in sorted(os.listdir(folder))
            if not name.startswith(".") and os.path.isdir(os.path.join(folder, name))]


def find_projects(root):
    """(name, folder, handoff path) for every project under root."""
    for name in subfolders(root):
        folder = os.path.join(root, name)
        handoff = handoff_in(folder)
        if handoff is not None:
            yield name, folder, handoff
            continue
        # .git is a folder in a repository and a file in a git worktree.
        if os.path.exists(os.path.join(folder, ".git")):
            continue
        try:
            inner_names = subfolders(folder)
        except OSError:
            continue  # one unreadable folder must not cost the whole table
        for inner in inner_names:
            inner_folder = os.path.join(folder, inner)
            inner_handoff = handoff_in(inner_folder)
            if inner_handoff is not None:
                # "/" on every system, so the row reads the same everywhere.
                yield f"{name}/{inner}", inner_folder, inner_handoff


def git_env():
    # Variables a git hook sets would point git at some other repository.
    return {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")}


def last_commit_time(folder):
    """Unix time of the last commit in this folder's own repository, or None.

    The folder has to contain .git itself; otherwise `git -C` would climb to
    an enclosing repository and report its commits. %ct is a plain integer
    whatever log.date says, and showSignature is switched off so signature
    lines cannot land in the output."""
    if not os.path.exists(os.path.join(folder, ".git")):
        return None
    out = subprocess.run(
        ["git", "-c", "log.showSignature=false", "-C", folder, "log", "-1", "--format=%ct"],
        capture_output=True, text=True, env=git_env())
    lines = out.stdout.strip().splitlines()
    if out.returncode != 0 or not lines or not lines[-1].isdigit():
        return None  # e.g. a repository with no commits yet
    return int(lines[-1])


def clean(value):
    # One row per project: tabs or newlines inside a value would break the table.
    return re.sub(r"[\t\r\n]+", " ", value)


def project_row(name, folder, handoff, today):
    fields = read_header(handoff)
    if fields is not None and fields.get("active", "").lower() == "no":
        return None
    known = fields if fields is not None else {}

    commit = last_commit_time(folder)
    commit_day = datetime.date.fromtimestamp(commit) if commit is not None else None
    handoff_day = datetime.date.fromtimestamp(os.path.getmtime(handoff))

    deadline = parse_date(known.get("deadline", ""))
    if deadline is not None and deadline >= today:
        deadline_text = str((deadline - today).days)
    else:
        deadline_text = ""   # none, unreadable, or passed: say nothing

    sessions_text = known.get("sessions_to_milestone", "") or "?"
    sessions = int(sessions_text) if sessions_text.isdigit() else None

    row = {
        "repo": name,
        "sessions_left": sessions_text,
        "days_since_commit": str((today - commit_day).days) if commit_day else "?",
        "deadline_in_days": deadline_text,
        "kind": known.get("kind", "") or "?",
        "stale": "STALE" if commit_day and handoff_day < commit_day else "",
        "next": known.get("next", "") or "?",
        # Headers written before 2026-11-24 call this line blocked_on.
        "waiting_for": known.get("waiting_for", known.get("blocked_on", "")),
    }
    # Fewest sessions first, unknown estimates last; then most recent commit,
    # with no commit counted as oldest; then the name.
    key = (sessions is None, sessions if sessions is not None else 0,
           commit is None, -(commit or 0), name)
    return key, row


def default_corpus_check():
    """Beside the corpus, wherever daily_archive.sh puts it."""
    corpus = os.environ.get("FIRST_READER_CORPUS") or "~/Claude_Transcript_Archive/corpus.jsonl"
    return os.path.join(os.path.dirname(os.path.expanduser(corpus)), "corpus_check.txt")


def warn_about_corpus(path):
    """Print one stderr line per month the transcript corpus is short."""
    try:
        with open(path) as fh:
            lines = [l.split() for l in fh if l.strip()]
    except OSError:
        return
    for parts in lines:
        if len(parts) == 4:
            month, source, n, found = parts
            where = "the archive" if source == "archive" else "Claude Code's folder"
            print(f"warning: the transcript corpus has {found} of your turns for {month}, "
                  f"against {n} in {where}; see ~/Library/Logs/claude-archive.log", file=sys.stderr)
        else:
            print(f"warning: the transcript corpus check reports: {' '.join(parts)}", file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description="List active projects, closest to completion first.")
    parser.add_argument("--root", default="~/repos", help="directory that holds the projects")
    parser.add_argument("--today", default=None, help="date to count from, YYYY-MM-DD (default: today)")
    parser.add_argument("--corpus-check", default=None,
                        help="file written by scripts/daily_archive.sh (default: corpus_check.txt "
                             "beside the transcript corpus)")
    args = parser.parse_args(argv)
    warn_about_corpus(args.corpus_check or default_corpus_check())

    root = os.path.expanduser(args.root)
    if not os.path.isdir(root):
        print(f"today.py: no such directory: {root}", file=sys.stderr)
        return 2
    if args.today is None:
        today = datetime.date.today()
    else:
        today = parse_date(args.today)
        if today is None:
            print(f"today.py: --today must be YYYY-MM-DD, got {args.today!r}", file=sys.stderr)
            return 2

    rows = []
    for name, folder, handoff in find_projects(root):
        result = project_row(name, folder, handoff, today)
        if result is not None:
            rows.append(result)
    rows.sort(key=lambda kr: kr[0])

    print("\t".join(COLUMNS))
    for _, row in rows:
        print("\t".join(clean(row[c]) for c in COLUMNS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
