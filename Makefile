# Test runner for the bundled skill scripts (verify_bib.py, style_scan.py).
# Each suite is stdlib-only (unittest) and offline, so `make test` runs on a
# bare python3 with no third-party dependencies and no network.

PYTHON ?= python3

.PHONY: test test-verify-citations test-style-audit

test: test-verify-citations test-style-audit

test-verify-citations:
	$(PYTHON) skills/verify-citations/tests/test_verify_bib.py

test-style-audit:
	$(PYTHON) skills/style-audit/tests/test_style_scan.py
