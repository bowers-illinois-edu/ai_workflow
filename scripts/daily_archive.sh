#!/bin/bash
# Daily maintenance for the Claude Code transcripts, run by launchd.
#
# Two steps, in this order. The archive comes first because it is the one that
# protects against loss: Claude Code prunes old sessions, and once a deletion
# reaches Backblaze and retention expires, nothing else holds them. The corpus
# refresh comes second, costs about a second, and keeps the file the
# first-reader persona is built from current.
#
# Both scripts are additive and safe to run while Claude Code is writing. A run
# that catches a partial last line is picked up by the next one.
#
# Install:  make install-archive-agent
# Log:      ~/Library/Logs/claude-archive.log

set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="$HOME/Library/Logs/claude-archive.log"
mkdir -p "$(dirname "$LOG")"

{
  /usr/bin/env python3 "$REPO/scripts/archive_transcripts.py"
  /usr/bin/env python3 "$REPO/skills/first-reader/scripts/mine_transcripts.py" --tail 0
} >>"$LOG" 2>&1

# Keep the log from growing without limit; a year of daily lines is plenty.
if [ -f "$LOG" ] && [ "$(wc -l <"$LOG")" -gt 800 ]; then
  tail -n 400 "$LOG" >"$LOG.trim" && mv "$LOG.trim" "$LOG"
fi
