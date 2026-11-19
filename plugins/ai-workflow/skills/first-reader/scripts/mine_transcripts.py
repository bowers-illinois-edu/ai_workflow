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

--root may also name the archive's projects folder,
~/Claude_Transcript_Archive/projects, which holds the same sessions gzipped
and keeps the ones Claude Code has deleted. The nightly job builds from there.

    python3 mine_transcripts.py --check corpus.jsonl \
        --root ~/Claude_Transcript_Archive/projects --live ~/.claude/projects

builds nothing. It prints one line, "month source turns-in-source
turns-in-corpus", for each month in which the corpus holds fewer turns than
the archive or Claude Code's folder, and exits 1 when there is any.

Output is one JSON object per line, sorted by timestamp:
    {"n", "ts", "project", "session", "model", "assistant", "human"}
where "model" names the model that wrote the assistant prose.

Exit status: 0 when the corpus is non-empty, 1 when it is empty (which
almost always means --root points somewhere with no transcripts, and a
silent empty file would read as "this person never complained").

Stdlib only, offline, no third-party dependencies.
"""

import argparse
import collections
import datetime
import glob
import gzip
import json
import os
import re
import sys
import zlib

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


# An archived copy is <session>.jsonl.gz. When Claude Code rewrites a session
# without growing it, archive_transcripts.py first keeps the old copy as
# <session>.<YYYY-MM-DD>.jsonl.gz, because the rewrite may have dropped text.
SNAPSHOT_DATE = re.compile(r"\.\d{4}-\d{2}-\d{2}$")


def session_files(root):
    """Session files directly under each project folder of root, plain or
    gzipped. Subagent transcripts sit one level deeper, under
    <project>/<session>/subagents/, and are left out: a turn there is a prompt
    one agent wrote to another, not something the person typed."""
    paths = glob.glob(os.path.join(root, "*", "*.jsonl"))
    paths += glob.glob(os.path.join(root, "*", "*.jsonl.gz"))
    return sorted(paths)


def session_id(path):
    """The bare session id, the same for the live file, its archived copy,
    and any dated snapshot, so rows from all three join to one session."""
    name = os.path.basename(path)
    for ending in (".jsonl.gz", ".jsonl"):
        if name.endswith(ending):
            name = name[:-len(ending)]
            break
    return SNAPSHOT_DATE.sub("", name)


def records_in(path):
    """Yield the JSON records of one session file, plain or gzipped.

    Transcripts are appended to live, so a half-written last line is normal
    and is skipped. A damaged gzip file yields what could be read before the
    damage, so one bad file never keeps the other sessions out of the corpus.
    """
    opener = gzip.open if path.endswith(".gz") else open
    try:
        with opener(path, "rt", errors="replace") as handle:
            for line in handle:
                try:
                    yield json.loads(line)
                except ValueError:
                    continue
    except (OSError, EOFError, zlib.error):
        return


def mine(root, since=None, project=None, tail=DEFAULT_TAIL):
    """Return the (assistant prose, human turn) pairs found under root.

    root is either Claude Code's own folder (~/.claude/projects) or the
    archive's projects folder, which holds the same sessions gzipped and keeps
    the ones Claude Code has deleted. Pairing is per session file. Walking one
    file in order and remembering the last assistant prose is enough, and it
    keeps sessions from contaminating each other, which matters when two
    sessions ran at once on the same project.

    A turn found in two copies of one session (a dated snapshot and the
    current copy) is one turn and is kept once.
    """
    pairs = []
    seen = set()
    for path in session_files(root):
        proj = os.path.basename(os.path.dirname(path))
        if project and project not in proj:
            continue
        session = session_id(path)
        previous_prose = ""
        previous_model = ""
        for rec in records_in(path):
            if rec.get("type") == "assistant":
                prose = text_of(rec.get("message")).strip()
                # A reply that is only a tool call carries no prose. Keeping
                # the previous prose, and the model that wrote it, is what
                # makes the pair meaningful for the many complaints that
                # follow a tool call.
                if prose:
                    previous_prose = prose
                    previous_model = (rec.get("message") or {}).get("model") or ""
                continue
            if not is_human_turn(rec):
                continue
            typed = text_of(rec.get("message")).strip()
            if not typed or is_machinery(typed):
                continue
            ts = rec.get("timestamp", "")
            if since and ts[:10] < since:
                continue
            key = (session, ts, typed)
            if key in seen:
                continue
            seen.add(key)
            pairs.append({"ts": ts, "project": proj, "session": session,
                          "model": previous_model,
                          "assistant": previous_prose[-tail:] if tail
                          else previous_prose,
                          "human": typed})

    pairs.sort(key=lambda r: r["ts"])
    for i, row in enumerate(pairs):
        row["n"] = i
    return pairs


def turns_by_month(rows):
    return collections.Counter(r["ts"][:7] for r in rows)


def check_corpus(corpus_path, archive_root, live_root):
    """Months where the corpus holds fewer turns than a source of them.

    Returns (month, source, turns in source, turns in corpus) for each short
    month, sorted. Two sources, because each catches a different failure:
    fewer than the archive means the corpus was built from the wrong place;
    fewer than Claude Code's folder means the archive step failed and new
    sessions are not being kept.

    Turns typed after the corpus was written are not missing from it, and the
    nightly job often runs while a session is open, so those are not counted.
    """
    corpus_rows = []
    written = ""
    if os.path.exists(corpus_path):
        with open(corpus_path) as fh:
            corpus_rows = [json.loads(l) for l in fh if l.strip()]
        written = datetime.datetime.fromtimestamp(
            os.path.getmtime(corpus_path), datetime.timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%S")
    in_corpus = turns_by_month(corpus_rows)

    short = []
    for source, root in (("archive", archive_root), ("live", live_root)):
        rows = [r for r in mine(root) if not written or r["ts"][:19] <= written]
        for month, n in turns_by_month(rows).items():
            if in_corpus.get(month, 0) < n:
                short.append((month, source, n, in_corpus.get(month, 0)))
    return sorted(short)


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
    parser.add_argument("--check", metavar="CORPUS",
                        help="build nothing; compare CORPUS month by month "
                             "with --root (the archive) and --live, print one "
                             "line per short month, exit 1 if any")
    parser.add_argument("--live", default=DEFAULT_ROOT,
                        help="Claude Code's own transcript folder, used by "
                             "--check (default: %(default)s)")
    args = parser.parse_args(argv)

    if args.check:
        short = check_corpus(os.path.expanduser(args.check),
                             os.path.expanduser(args.root),
                             os.path.expanduser(args.live))
        for month, source, n, found in short:
            print("%s %s %d %d" % (month, source, n, found))
        return 1 if short else 0

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
