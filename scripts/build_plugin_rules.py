#!/usr/bin/env python3
"""Refresh the rules the Claude Code plugin prints at session start.

A collaborator who installs the `ai-workflow` plugin has no CLAUDE.md, and a
plugin cannot ship one. The plugin's SessionStart hook prints
plugins/ai-workflow/rules/coding.md into context instead, once per session.
That file is a copy of CLAUDE_CODING.md, and a copy drifts unless something
rewrites it, so `make plugins` runs this script and
scripts/tests/test_plugin_rules_hook.py fails when the copy is behind.

The copy is verbatim rather than a translation. CLAUDE_CODING.md is written as
instructions to the assistant with "me" meaning whoever is in the session, and
that reads correctly for a collaborator.

Stdlib only.
"""

import os
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = os.path.join(REPO_ROOT, "plugins", "ai-workflow", "rules")

# destination name under rules/ -> source path
COPIES = {
    "coding.md": os.path.join(REPO_ROOT, "CLAUDE_CODING.md"),
}


def build(rules_dir):
    """Write every copy into `rules_dir`. The argument exists so a test can
    build into a temporary directory instead of the tracked one."""
    os.makedirs(rules_dir, exist_ok=True)
    for name, source in COPIES.items():
        shutil.copyfile(source, os.path.join(rules_dir, name))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else RULES)
