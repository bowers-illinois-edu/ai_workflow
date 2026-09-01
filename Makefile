# Test runner for the bundled scripts (verify_bib.py, style_scan.py,
# check_claude_app.py). Each suite is stdlib-only (unittest) and offline, so
# `make test` runs on a bare python3 with no third-party dependencies and no
# network.
#
# `make check-claude-app` is separate because it reads the git log rather than
# running offline: it reports whether CLAUDE.md or CLAUDE_CODING.md has moved
# since each claude_app block was last synced by hand.

PYTHON ?= python3

.PHONY: test test-verify-citations test-style-audit test-style-gate test-first-reader test-archive test-claude-app test-chatgpt-plugin test-install-links check-claude-app app-skills archive install install-dry-run install-archive-agent uninstall-archive-agent

test: test-verify-citations test-style-audit test-style-gate test-first-reader test-archive test-claude-app test-chatgpt-plugin test-install-links

test-verify-citations:
	$(PYTHON) skills/verify-citations/tests/test_verify_bib.py

test-style-audit:
	$(PYTHON) skills/style-audit/tests/test_style_scan.py

test-style-gate:
	$(PYTHON) skills/style-audit/tests/test_style_gate.py

test-first-reader:
	$(PYTHON) skills/first-reader/tests/test_mine_transcripts.py

test-archive:
	$(PYTHON) scripts/tests/test_archive_transcripts.py

test-claude-app:
	$(PYTHON) scripts/tests/test_check_claude_app.py

test-chatgpt-plugin:
	$(PYTHON) scripts/tests/test_chatgpt_plugin.py

test-install-links:
	$(PYTHON) scripts/tests/test_install_links.py

check-claude-app:
	$(PYTHON) scripts/check_claude_app.py

# The Claude app takes a skill as a zipped folder whose root is the folder
# itself. `zip` does that directly, so this needs no script and no tests.
#
# Two of these skills reach the Claude Code originals by symlink rather than by
# copy: style-audit/scripts/ points at the one directory holding style_scan.py,
# and math/references/ at the one directory holding sections 4-16. `zip -r`
# stores what a symlink points at, so each upload carries the same files the
# Claude Code skill uses and there is never a second copy to go stale.
app-skills:
	rm -rf claude_app/dist && mkdir -p claude_app/dist
	cd claude_app/skills && for s in */; do zip -qr "../dist/$${s%/}.zip" "$${s%/}" -x '*__pycache__*'; done
	@ls -l claude_app/dist

# The transcripts in ~/.claude/projects are the source the corpus and the
# first-reader persona both derive from, and Claude Code prunes them on its own
# schedule. Backblaze mirrors the disk but drops what the disk drops, so this
# archive is additive: it never deletes, and a pruned session survives in it.
# `archive` also refreshes the corpus, which costs about a second.
archive:
	./scripts/daily_archive.sh && tail -2 ~/Library/Logs/claude-archive.log

# Claude Code reads ~/.claude; this repository lives somewhere else. On a new
# machine `make install` is the one command that connects them, replacing ten
# symlinks that were previously made by hand. It never touches a link pointing
# outside this repository, and it stops rather than replace a real file, so it
# is safe to run on a machine that is already set up. `make install-dry-run`
# reports what it would do and changes nothing.
install:
	$(PYTHON) scripts/install_links.py

install-dry-run:
	$(PYTHON) scripts/install_links.py --dry-run

install-archive-agent:
	@mkdir -p ~/Library/LaunchAgents
	@sed -e 's|__REPO__|$(CURDIR)|g' -e 's|__HOME__|$(HOME)|g' \
	    scripts/com.jake.claude-archive.plist \
	    > ~/Library/LaunchAgents/com.jake.claude-archive.plist
	@launchctl unload ~/Library/LaunchAgents/com.jake.claude-archive.plist 2>/dev/null || true
	launchctl load ~/Library/LaunchAgents/com.jake.claude-archive.plist
	@echo "installed: runs daily at 09:30, logs to ~/Library/Logs/claude-archive.log"

uninstall-archive-agent:
	launchctl unload ~/Library/LaunchAgents/com.jake.claude-archive.plist
	rm -f ~/Library/LaunchAgents/com.jake.claude-archive.plist
