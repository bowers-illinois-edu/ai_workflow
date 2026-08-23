# Test runner for the bundled scripts (verify_bib.py, style_scan.py,
# check_claude_app.py). Each suite is stdlib-only (unittest) and offline, so
# `make test` runs on a bare python3 with no third-party dependencies and no
# network.
#
# `make check-claude-app` is separate because it reads the git log rather than
# running offline: it reports whether CLAUDE.md or CLAUDE_CODING.md has moved
# since each claude_app block was last synced by hand.

PYTHON ?= python3

.PHONY: test test-verify-citations test-style-audit test-claude-app check-claude-app app-skills

test: test-verify-citations test-style-audit test-claude-app

test-verify-citations:
	$(PYTHON) skills/verify-citations/tests/test_verify_bib.py

test-style-audit:
	$(PYTHON) skills/style-audit/tests/test_style_scan.py

test-claude-app:
	$(PYTHON) scripts/tests/test_check_claude_app.py

check-claude-app:
	$(PYTHON) scripts/check_claude_app.py

# The Claude app takes a skill as a zipped folder whose root is the folder
# itself. `zip` does that directly, so this needs no script and no tests.
#
# style-audit ships the scanner, which is copied in here rather than kept in a
# second place under claude_app/: one copy of style_scan.py in the repository
# means it cannot drift from the one the Claude Code skill runs.
app-skills:
	rm -rf claude_app/dist && mkdir -p claude_app/dist/stage
	cp -R claude_app/skills/. claude_app/dist/stage/
	mkdir -p claude_app/dist/stage/style-audit/scripts
	cp skills/style-audit/scripts/style_scan.py claude_app/dist/stage/style-audit/scripts/
	cd claude_app/dist/stage && for s in */; do zip -qr "../$${s%/}.zip" "$${s%/}"; done
	rm -rf claude_app/dist/stage
	@ls -l claude_app/dist
