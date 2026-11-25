#!/bin/bash
# Daily maintenance for the Claude Code transcripts, run by launchd.
#
# Three steps, in this order. The archive comes first because it is the one
# that protects against loss: Claude Code prunes old sessions, and once a
# deletion reaches Backblaze and retention expires, nothing else holds them.
# The corpus is rebuilt second, from the archive and not from
# ~/.claude/projects, because only the archive still holds the sessions Claude
# Code has deleted. Until 2026-11-19 it was built from ~/.claude/projects and
# had silently lost August and September.
#
# The third step counts Jake's turns per month in the corpus, the archive, and
# ~/.claude/projects, and reports any month where the corpus is short. Jake
# chose on 2026-11-19 to hear about a short month in two places: a Mac
# notification that opens a note saying what to do, and a warning from the
# `today` skill, which reads corpus_check.txt beside the corpus.
#
# Every step is additive and safe to run while Claude Code is writing. A run
# that catches a partial last line is picked up by the next one.
#
# Install:  make install-archive-agent
# Log:      ~/Library/Logs/claude-archive.log

set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="$HOME/Library/Logs/claude-archive.log"
mkdir -p "$(dirname "$LOG")"

# The same defaults the two Python scripts use, so all three agree on where
# the archive and the corpus are.
ARCHIVE="${CLAUDE_TRANSCRIPT_ARCHIVE:-$HOME/Claude_Transcript_Archive}"
CORPUS="${FIRST_READER_CORPUS:-$HOME/Claude_Transcript_Archive/corpus.jsonl}"
CHECK="$(dirname "$CORPUS")/corpus_check.txt"
MINE="$REPO/skills/first-reader/scripts/mine_transcripts.py"

{
  /usr/bin/env python3 "$REPO/scripts/archive_transcripts.py"
  /usr/bin/env python3 "$MINE" --root "$ARCHIVE/projects" --tail 0 --out "$CORPUS"
} >>"$LOG" 2>&1

mkdir -p "$(dirname "$CHECK")"
/usr/bin/env python3 "$MINE" --check "$CORPUS" --root "$ARCHIVE/projects" \
  --live "$HOME/.claude/projects" >"$CHECK.partial" 2>>"$LOG"
status=$?
mv "$CHECK.partial" "$CHECK"

# Jake, 2026-11-19: a click on the notification should land him where his
# next action is clear. So a short month gets a note naming it and the one
# thing to do, in his Obsidian vault when there is one and beside the corpus
# otherwise, and the notification opens that note.
VAULT="$HOME/Documents/Obsidian Vault"
if [ -d "$VAULT" ]; then
  NOTE="$VAULT/transcript_corpus_check.md"
else
  NOTE="$(dirname "$CORPUS")/transcript_corpus_check.md"
fi

if [ "$status" -ne 0 ]; then
  months="$(cut -d' ' -f1 "$CHECK" | sort -u | tr '\n' ' ')"
  months="${months% }"
  message="The transcript corpus is missing turns for $months. Click for what to do."
  { echo "corpus check: missing turns for $months"; cat "$CHECK"; } >>"$LOG"
  cat >"$NOTE" <<NOTE_END
# Transcript corpus is missing turns

Written by scripts/daily_archive.sh on $(date '+%Y-%m-%d at %H:%M').

The nightly check found fewer of your turns in
$CORPUS than in the transcripts for: $months.

Each line of $CHECK reads: month, where the turns were counted (archive or
live, meaning Claude Code's own folder), turns there, turns in the corpus.

$(cat "$CHECK")

What to do: open a Ghostty tab and run

    cd ~/repos/ai_workflow && claude

then ask Claude Code to read $CHECK and
~/Library/Logs/claude-archive.log and fix what they report. This note is
deleted the first night nothing is short.
NOTE_END
  if [ -n "${CLAUDE_ARCHIVE_NOTIFY:-}" ]; then
    "$CLAUDE_ARCHIVE_NOTIFY" "$message" "$NOTE"
  else
    # launchd's PATH has no Homebrew folder, so look there by name too.
    notifier="$(command -v terminal-notifier || echo /opt/homebrew/bin/terminal-notifier)"
    if [ -d "$VAULT" ]; then
      url="obsidian://open?path=$(/usr/bin/python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$NOTE")"
    else
      url="file://$NOTE"
    fi
    if [ -x "$notifier" ]; then
      "$notifier" -title "Claude transcript archive" -message "$message" -open "$url" >>"$LOG" 2>&1
    else
      /usr/bin/osascript -e "display notification \"$message\" with title \"Claude transcript archive\"" \
        >>"$LOG" 2>&1
    fi
  fi
else
  rm -f "$NOTE"
fi

# Jake's private repository may hold a job that needs the fresh corpus. A
# failure there must not change the status of the archive.
EXTRA="${CLAUDE_ARCHIVE_EXTRA:-$HOME/repos/ai_workflow_private/writing_page/nightly.sh}"
if [ -x "$EXTRA" ]; then
  "$EXTRA" >>"$LOG" 2>&1 || echo "extra nightly job failed: $EXTRA" >>"$LOG"
fi

# Keep the log from growing without limit; a year of daily lines is plenty.
if [ -f "$LOG" ] && [ "$(wc -l <"$LOG")" -gt 800 ]; then
  tail -n 400 "$LOG" >"$LOG.trim" && mv "$LOG.trim" "$LOG"
fi

exit "$status"
