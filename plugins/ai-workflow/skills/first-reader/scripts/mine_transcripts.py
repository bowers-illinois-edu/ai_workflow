#!/usr/bin/env python3
"""Build a (prose, reaction) corpus from Claude Code transcripts.

Claude Code appends every session to a JSONL file under
~/.claude/projects/<flattened-cwd>/<session-id>.jsonl. Most records in those
files are machinery: tool calls, tool results, slash-command echoes,
notifications from other agents, injected reminders. This script pulls out
the two kinds of record that carry evidence about how a person reads, and
pairs them:

  * every turn the person actually typed, and
  * the assistant prose that immediately preceded it.

The pair is the unit of evidence. A complaint on its own ("what family?")
records the objection but not the sentence that caused it, and a persona
built from objections alone learns a vocabulary of complaint rather than a
set of failures to look for.

Usage:
    python3 mine_transcripts.py                       # writes the Dropbox corpus
    python3 mine_transcripts.py --out corpus.jsonl    # or anywhere you name
    python3 mine_transcripts.py --root ~/.claude/projects --since 2026-06-01 \
        --project fully-specified --tail 4000 --out corpus.jsonl

With no --out the corpus goes to ~/Claude_Transcript_Archive/corpus.jsonl, or
to $FIRST_READER_CORPUS if that is set. It is kept out of both repositories on
purpose, and out of ~/Library/CloudStorage, where macOS would deny a scheduled
job access. See default_corpus_path below.

Output is one JSON object per line, sorted by timestamp:
    {"n", "ts", "project", "session", "assistant", "human"}

Exit status: 0 when the corpus is non-empty, 1 when it is empty (which
almost always means --root points somewhere with no transcripts, and a
silent empty file would read as "this person never complained").

Stdlib only, offline, no third-party dependencies.
"""

import argparse
import glob
import json
import os
import sys

DEFAULT_ROOT = os.path.expanduser("~/.claude/projects")
DEFAULT_TAIL = 2500

# Where the corpus lives when --out is not given. It belongs in neither
# repository: it spans every project the person has used Claude Code on, so it
# holds other people's unpublished work, students' job materials, confidential
# peer reviews, and personal notes.
#
# It also must not sit under ~/Library/CloudStorage. macOS denies a launchd job
# access there, so a scheduled refresh would fail every night while still
# working when run by hand. A plain home directory works for background jobs
# and is picked up by whole-disk backup.
CORPUS_DIRNAME = "Claude_Transcript_Archive"

# Text the person "sent" that they did not write as prose. Each is injected by
# the harness or by another agent, so none of it is evidence about reading.
MACHINERY_PREFIXES = (
    "<local-command",
    "<command-name",
    "<command-message",
    "<command-args",
    "<user-memory",
    "<system-reminder",
    "<bash-",
    "[Request interrupted",
    "Caveat:",
    "Another Claude session",
)


def text_of(msg):
    """Prose in one message record, ignoring tool calls and tool results.

    The harness stores content either as a bare string or as a list of typed
    blocks. Only "text" blocks are prose; a tool_result is data the person
    never read as writing, and counting it as prose would put transcript
    noise into the corpus.
    """
    content = (msg or {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text")
    return ""


def is_machinery(text):
    """True when the text was injected rather than typed."""
    return text.lstrip().startswith(MACHINERY_PREFIXES)


def is_human_turn(rec):
    """True when a person typed this record.

    Recent records carry origin.kind == "human", which is decisive: it
    separates a typed turn from a task notification or a message forwarded
    from another agent. Older records predate that field, so promptSource
    stands in for them.
    """
    if rec.get("type") != "user" or rec.get("isMeta"):
        return False
    origin = (rec.get("origin") or {}).get("kind")
    if origin is not None:
        return origin == "human"
    return bool(rec.get("promptSource"))


def mine(root, since=None, project=None, tail=DEFAULT_TAIL):
    """Return the (assistant prose, human turn) pairs found under root.

    Pairing is per session file. Walking one file in order and remembering
    the last assistant prose is enough, and it keeps sessions from
    contaminating each other, which matters when two sessions ran at once on
    the same project.
    """
    pairs = []
    for path in sorted(glob.glob(os.path.join(root, "*", "*.jsonl"))):
        proj = os.path.basename(os.path.dirname(path))
        if project and project not in proj:
            continue
        session = os.path.basename(path)[:-6]
        previous_prose = ""
        try:
            handle = open(path, "r", errors="replace")
        except OSError:
            continue
        with handle:
            for line in handle:
                try:
                    rec = json.loads(line)
                except ValueError:
                    # Transcripts are appended to live, so the last line of an
                    # active session is often half-written. Skipping it is
                    # right; aborting the run over it is not.
                    continue
                if rec.get("type") == "assistant":
                    prose = text_of(rec.get("message")).strip()
                    # A reply that is only a tool call carries no prose. Keeping
                    # the previous prose is what makes the pair meaningful for
                    # the many complaints that follow a tool call.
                    if prose:
                        previous_prose = prose
                    continue
                if not is_human_turn(rec):
                    continue
                typed = text_of(rec.get("message")).strip()
                if not typed or is_machinery(typed):
                    continue
                ts = rec.get("timestamp", "")
                if since and ts[:10] < since:
                    continue
                pairs.append({"ts": ts, "project": proj, "session": session,
                              "assistant": previous_prose[-tail:] if tail
                              else previous_prose,
                              "human": typed})

    pairs.sort(key=lambda r: r["ts"])
    for i, row in enumerate(pairs):
        row["n"] = i
    return pairs


def default_corpus_path(env=None, home=None):
    """Where to write the corpus when the caller does not say.

    An explicit FIRST_READER_CORPUS wins, so a machine that keeps it elsewhere
    needs no flag. Otherwise it sits beside the transcript archive in the home
    directory, which a scheduled job can write and whole-disk backup covers.
    """
    env = os.environ if env is None else env
    explicit = env.get("FIRST_READER_CORPUS")
    if explicit:
        return os.path.expanduser(explicit)
    home = home or os.path.expanduser("~")
    return os.path.join(home, CORPUS_DIRNAME, "corpus.jsonl")


def main(argv=None, home=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--root", default=DEFAULT_ROOT,
                        help="transcript directory (default: %(default)s)")
    parser.add_argument("--out", help="output JSONL path (default: the corpus "
                                     "in Dropbox, or $FIRST_READER_CORPUS)")
    parser.add_argument("--since", help="keep turns on or after YYYY-MM-DD")
    parser.add_argument("--project", help="substring filter on project folder")
    parser.add_argument("--tail", type=int, default=DEFAULT_TAIL,
                        help="characters of preceding prose to keep "
                             "(default: %(default)s; 0 keeps all)")
    args = parser.parse_args(argv)

    out = args.out or default_corpus_path(home=home)
    parent = os.path.dirname(os.path.abspath(out))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)

    rows = mine(os.path.expanduser(args.root), since=args.since,
                project=args.project, tail=args.tail)
    with open(out, "w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")

    if not rows:
        sys.stderr.write(
            "no turns found under %s --- check the path\n" % args.root)
        return 1

    chars = sum(len(r["human"]) for r in rows)
    projects = len(set(r["project"] for r in rows))
    sys.stderr.write(
        "%d turns, %s to %s, %d projects, %d characters -> %s\n"
        % (len(rows), rows[0]["ts"][:10], rows[-1]["ts"][:10], projects,
           chars, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
