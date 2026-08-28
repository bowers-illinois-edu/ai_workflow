#!/usr/bin/env python3
"""Keep a permanent, additive archive of the Claude Code transcripts.

This is not a backup. Backblaze already mirrors the disk, so a dead laptop is
covered. A mirror cannot help with the other way transcripts are lost: Claude
Code prunes old sessions on its own schedule, and once a deletion propagates
and retention expires, the mirror has dropped them too.

That matters here because the transcripts are the source everything else
derives from. The corpus is rebuilt from them in a second, and the persona in
`skills/first-reader/` is written from the corpus. Neither can be rebuilt or
refreshed once the transcripts are gone.

So this archive is additive. It never deletes, and it never overwrites content
it cannot prove it still holds:

  * A source file that grew is an append, which is how JSONL written a line at
    a time normally changes. The archived copy is replaced.
  * A source file that changed without growing is a rewrite or a truncation.
    The old archived copy is snapshot under a dated name first, so no text is
    lost even if the new one is shorter.
  * A source file that vanished was pruned. Its archived copy stays. This is
    the event the script exists for.

Files are stored gzipped in a mirror of the source tree, one file per session,
so any single session can be read back without unpacking the whole archive:

    <dest>/projects/<project>/<session>.jsonl.gz
    <dest>/manifest.json

Reading happens while Claude Code may be appending to the same files. A run
therefore sometimes captures a partial last line, which the next run picks up
once the file has grown.

Usage:
    python3 archive_transcripts.py                  # to the Dropbox archive
    python3 archive_transcripts.py --dest /somewhere/else
    python3 archive_transcripts.py --source ~/.claude/projects --dest DIR

With no --dest the archive goes to ~/Claude_Transcript_Archive, or to
$CLAUDE_TRANSCRIPT_ARCHIVE when that is set. It is deliberately not under
~/Library/CloudStorage, where macOS would deny a scheduled job access.

Exit status: 0 on success, 2 when the source is missing or there is nowhere
to write. A missing source is an error rather than an empty archive, because
an empty archive reads as "nothing to keep."

Stdlib only, offline, no third-party dependencies.

Restore one session:  gunzip -c <archive>/projects/<proj>/<sess>.jsonl.gz
Restore everything:   cd <archive>/projects && find . -name '*.jsonl.gz' -exec gunzip -k {} +
"""

import argparse
import datetime
import gzip
import hashlib
import json
import os
import shutil
import sys

DEFAULT_SOURCE = os.path.expanduser("~/.claude/projects")
# Not under ~/Library/CloudStorage: macOS denies a launchd job access there, so
# a scheduled archive would fail every night while working when run by hand.
# A plain home directory works for background jobs, and whole-disk backup
# (Backblaze here) carries it off the machine.
ARCHIVE_DIRNAME = "Claude_Transcript_Archive"


def default_archive_path(env=None, home=None):
    """Where the archive goes when the caller does not say.

    The same rule as the corpus miner uses, and for the same reason.
    """
    env = os.environ if env is None else env
    explicit = env.get("CLAUDE_TRANSCRIPT_ARCHIVE")
    if explicit:
        return os.path.expanduser(explicit)
    home = home or os.path.expanduser("~")
    return os.path.join(home, ARCHIVE_DIRNAME)


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(dest):
    path = os.path.join(dest, "manifest.json")
    if not os.path.exists(path):
        return {"files": {}}
    try:
        with open(path) as fh:
            data = json.load(fh)
    except (ValueError, OSError):
        # A manifest damaged mid-write must not stop the archive; rebuilding it
        # costs one pass in which everything looks new. An unreadable one is
        # caught here too, so the writability check below reports the real
        # problem instead of a traceback from this line.
        return {"files": {}}
    data.setdefault("files", {})
    return data


def compress_to(src_path, out_path):
    """Write a gzip copy, via a temporary file so a crash leaves no half copy."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tmp = out_path + ".partial"
    with open(src_path, "rb") as src, gzip.open(tmp, "wb", compresslevel=6) as out:
        shutil.copyfileobj(src, out, length=1 << 20)
    os.replace(tmp, out_path)


def archive(source, dest, today=None):
    """Copy every changed transcript into dest. Return counts.

    Nothing in dest is ever removed, so the archive accumulates sessions the
    source no longer has.
    """
    today = today or datetime.date.today().isoformat()
    manifest = load_manifest(dest)
    files = manifest["files"]
    stats = {"archived": 0, "skipped": 0, "snapshotted": 0, "failed": 0,
             "retained": 0, "bytes_in": 0}

    seen = set()
    for root, _dirs, names in os.walk(source):
        for name in sorted(names):
            if not name.endswith(".jsonl"):
                continue
            src_path = os.path.join(root, name)
            rel = os.path.relpath(src_path, source)
            seen.add(rel)
            try:
                size = os.path.getsize(src_path)
                digest = sha256_of(src_path)
            except OSError:
                stats["failed"] += 1
                continue

            previous = files.get(rel)
            if previous and previous.get("sha256") == digest:
                stats["skipped"] += 1
                continue

            out_path = os.path.join(dest, "projects", rel + ".gz")

            # A file that did not grow but changed may have lost text, so keep
            # what is already archived before replacing it.
            if previous and os.path.exists(out_path) and size <= previous.get("size", 0):
                snap = os.path.join(
                    dest, "projects",
                    rel[:-len(".jsonl")] + "." + previous.get("last_archived", today)
                    + ".jsonl.gz")
                if not os.path.exists(snap):
                    shutil.copy2(out_path, snap)
                    stats["snapshotted"] += 1

            try:
                compress_to(src_path, out_path)
            except OSError:
                stats["failed"] += 1
                continue

            files[rel] = {
                "size": size,
                "sha256": digest,
                "mtime": os.path.getmtime(src_path),
                "first_archived": (previous or {}).get("first_archived", today),
                "last_archived": today,
            }
            stats["archived"] += 1
            stats["bytes_in"] += size

    stats["retained"] = sum(1 for rel in files if rel not in seen)

    os.makedirs(dest, exist_ok=True)
    manifest["updated"] = today
    manifest["sessions"] = len(files)
    tmp = os.path.join(dest, "manifest.json.partial")
    with open(tmp, "w") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
    os.replace(tmp, os.path.join(dest, "manifest.json"))
    return stats


def main(argv=None, home=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--source", default=DEFAULT_SOURCE,
                        help="transcript directory (default: %(default)s)")
    parser.add_argument("--dest",
                        help="archive directory (default: the Dropbox archive, "
                             "or $CLAUDE_TRANSCRIPT_ARCHIVE)")
    args = parser.parse_args(argv)

    source = os.path.expanduser(args.source)
    if not os.path.isdir(source):
        sys.stderr.write("no transcript directory at %s\n" % source)
        return 2

    dest = os.path.expanduser(args.dest or default_archive_path(home=home))

    # macOS gives a launchd process none of the Full Disk Access a terminal
    # inherits, so ~/Library/CloudStorage reads as "Operation not permitted"
    # from a background job even though it works by hand. Check once, and say
    # what to do, rather than failing file by file into a log nobody reads.
    try:
        os.makedirs(dest, exist_ok=True)
        probe = os.path.join(dest, ".write-probe")
        with open(probe, "w") as fh:
            fh.write("ok")
        os.remove(probe)
    except OSError as exc:
        sys.stderr.write(
            "cannot write to %s: %s\n"
            "If this ran from launchd or cron and works by hand, the cause is "
            "Full Disk Access: grant it to the program in System Settings, "
            "Privacy and Security, or point --dest outside "
            "~/Library/CloudStorage.\n" % (dest, exc))
        return 2

    stats = archive(source, dest)
    sys.stderr.write(
        "%s: %d archived (%.1f MB read), %d unchanged, %d snapshotted, "
        "%d kept after deletion, %d unreadable -> %s\n"
        % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
           stats["archived"], stats["bytes_in"] / 1048576.0, stats["skipped"],
           stats["snapshotted"], stats["retained"], stats["failed"], dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
