# Test runner for the bundled scripts and the packaging around them. Each
# suite is stdlib-only (unittest) and offline, so `make test` runs on a bare
# python3 with no third-party dependencies and no network.
#
# `make check-claude-app` is separate because it reads the git log rather than
# running offline: it reports whether CLAUDE.md or CLAUDE_CODING.md has moved
# since each claude_app block was last synced by hand.

PYTHON ?= python3

.PHONY: test test-verify-citations test-style-audit test-style-gate test-first-reader test-archive test-claude-app test-chatgpt-plugin test-install-links test-build-agents-md test-plugins test-codex-hooks check-claude-app agents-md plugins app-skills archive install install-dry-run install-archive-agent uninstall-archive-agent

test: test-verify-citations test-style-audit test-style-gate test-first-reader test-archive test-claude-app test-chatgpt-plugin test-install-links test-build-agents-md test-plugins test-codex-hooks

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

test-build-agents-md:
	$(PYTHON) scripts/tests/test_build_agents_md.py

test-plugins:
	$(PYTHON) scripts/tests/test_plugins_self_contained.py

test-codex-hooks:
	$(PYTHON) scripts/tests/test_codex_hooks.py

check-claude-app:
	$(PYTHON) scripts/check_claude_app.py

# Codex reads one AGENTS.md and follows no import lines, so it gets CLAUDE.md
# with the two files CLAUDE.md imports written out in place. The built file is
# tracked, and test-build-agents-md fails when it is behind its sources.
agents-md:
	$(PYTHON) scripts/build_agents_md.py

# The plugin directories hold the real files, because Codex and ChatGPT copy a
# plugin directory without following symlinks. Two directories have to exist
# in both plugins, the math references and the style-audit scripts. The Claude
# Code plugin holds the originals and the app plugin holds copies; this target
# refreshes the copies, and test-plugins fails when they differ.
plugins:
	rsync -a --delete --exclude __pycache__ --exclude .DS_Store \
	    plugins/ai-workflow/skills/math/references/ \
	    plugins/ai-workflow-app/skills/math/references/
	rsync -a --delete --exclude __pycache__ --exclude .DS_Store \
	    plugins/ai-workflow/skills/style-audit/scripts/ \
	    plugins/ai-workflow-app/skills/style-audit/scripts/

# The Claude app takes a skill as a zipped folder whose root is the folder
# itself. `zip` does that directly, so this needs no script and no tests. The
# zip is built from the plugin directory, where the files live; the output
# path is absolute because the shell's `cd` through a symlink and the kernel's
# idea of `..` disagree.
app-skills: plugins
	rm -rf claude_app/dist && mkdir -p claude_app/dist
	cd plugins/ai-workflow-app/skills && for s in */; do zip -qr "$(CURDIR)/claude_app/dist/$${s%/}.zip" "$${s%/}" -x '*__pycache__*' -x '*.DS_Store'; done
	@ls -l claude_app/dist

# The transcripts in ~/.claude/projects are the source the corpus and the
# first-reader persona both derive from, and Claude Code prunes them on its own
# schedule. Backblaze mirrors the disk but drops what the disk drops, so this
# archive is additive: it never deletes, and a pruned session survives in it.
# `archive` also refreshes the corpus, which costs about a second.
archive:
	./scripts/daily_archive.sh && tail -2 ~/Library/Logs/claude-archive.log

# Claude Code reads ~/.claude and Codex reads ~/.codex; this repository lives
# somewhere else. On a new machine `make install` is the one command that
# connects them. It never touches a link pointing outside this repository, it
# stops rather than replace a real file, and it writes Codex's hooks.json only
# when no hooks file is there or the one there already runs the style gate, so
# it is safe to run on a machine that is already set up. `make
# install-dry-run` reports what it would do and changes nothing. The Codex
# links go in only when ~/.codex exists.
install: agents-md
	$(PYTHON) scripts/install_links.py --codex-hooks

install-dry-run:
	$(PYTHON) scripts/install_links.py --codex-hooks --dry-run

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
