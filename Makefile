# Test runner for the bundled scripts (verify_bib.py, style_scan.py,
# check_claude_app.py). Each suite is stdlib-only (unittest) and offline, so
# `make test` runs on a bare python3 with no third-party dependencies and no
# network.
#
# `make check-claude-app` is separate because it reads the git log rather than
# running offline: it reports whether CLAUDE.md or CLAUDE_CODING.md has moved
# since each claude_app block was last synced by hand.

PYTHON ?= python3

.PHONY: test test-verify-citations test-style-audit test-claude-app check-claude-app

test: test-verify-citations test-style-audit test-claude-app

test-verify-citations:
	$(PYTHON) skills/verify-citations/tests/test_verify_bib.py

test-style-audit:
	$(PYTHON) skills/style-audit/tests/test_style_scan.py

test-claude-app:
	$(PYTHON) scripts/tests/test_check_claude_app.py

check-claude-app:
	$(PYTHON) scripts/check_claude_app.py
