# Test runner for the bundled scripts (verify_bib.py, style_scan.py,
# check_claude_app.py). Each suite is stdlib-only (unittest) and offline, so
# `make test` runs on a bare python3 with no third-party dependencies and no
# network.
#
# `make check-claude-app` is separate because it reads the git log rather than
# running offline: it reports whether CLAUDE.md or CLAUDE_CODING.md has moved
# since each claude_app block was last synced by hand.

PYTHON ?= python3

.PHONY: test test-verify-citations test-style-audit test-first-reader test-claude-app check-claude-app app-skills

test: test-verify-citations test-style-audit test-first-reader test-claude-app

test-verify-citations:
	$(PYTHON) skills/verify-citations/tests/test_verify_bib.py

test-style-audit:
	$(PYTHON) skills/style-audit/tests/test_style_scan.py

test-first-reader:
	$(PYTHON) skills/first-reader/tests/test_mine_transcripts.py

test-claude-app:
	$(PYTHON) scripts/tests/test_check_claude_app.py

check-claude-app:
	$(PYTHON) scripts/check_claude_app.py

# The Claude app takes a skill as a zipped folder whose root is the folder
# itself. `zip` does that directly, so this needs no script and no tests.
#
# style-audit ships the scanner. Its scripts/ is a symlink to the one directory
# that holds style_scan.py, and `zip -r` stores what a symlink points at, so
# the upload carries the same scanner the Claude Code skill runs and there is
# never a second copy to go stale.
app-skills:
	rm -rf claude_app/dist && mkdir -p claude_app/dist
	cd claude_app/skills && for s in */; do zip -qr "../dist/$${s%/}.zip" "$${s%/}" -x '*__pycache__*'; done
	@ls -l claude_app/dist
