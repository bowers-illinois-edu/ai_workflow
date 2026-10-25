"""Tests for skills/today/scripts/today.py.

today.py answers one question at the start of a research morning: which
active project is closest to completion, and what is its next step. It reads
a short header at the top of each repository's HANDOFF.md and the date of the
repository's last commit, and prints a tab-separated table that the `today`
skill reads before offering Jake at most three options. The tests check the
decisions Jake made on 2026-10-25:

- Only a header line `active: no` removes a project. There is no time cutoff,
  because Jake returns to projects after a year or more.
- The table orders projects by the session's own estimate of sessions left,
  fewest first, so that his rule "work on whatever is closest to completion"
  can be applied by reading the top of the table. Ties go to the project with
  the most recent commit, because he will remember more of it.
- A deadline is optional. It shows as days remaining and does not change the
  order. A passed deadline shows as blank and its date does not appear at all,
  because an overdue count is what made Todoist and GitHub Issues into lists
  he stopped opening, and an agent shown the raw date would compute the count.
- A header written on an earlier day than the last commit is marked STALE.
  A header written the same day is current, because sessions usually write
  HANDOFF.md a minute before committing.
- An error is an error: a missing root directory exits nonzero instead of
  printing an empty table, which an agent would report as "no projects."

The test date is 2024-02-27, not the real date, so an implementation that
ignores --today and reads the clock fails. All dates are local calendar days
in a fixed time zone set below.

Stdlib only, offline, Python 3.9 or later, matching the other suites here.
"""

import csv
import datetime
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

# Fix the time zone for this process and every subprocess, so commit times,
# file times, and "days since" are computed in one zone whatever the machine's.
os.environ["TZ"] = "America/Chicago"
time.tzset()
# If the machine lacks the zone file, Python and git fall back to UTC without
# an error, and the late-night test would pass an implementation that counts
# in UTC. Stop instead.
assert time.strftime("%z", time.localtime(time.mktime((2024, 2, 27, 12, 0, 0, 0, 0, -1)))) == "-0600", \
    "America/Chicago time zone data is missing on this machine"

# The script is bundled with the `today` skill: skills/today/scripts/today.py.
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(SKILL_DIR, "scripts", "today.py")
TODAY = datetime.date(2024, 2, 27)
HEADER_ROW = "repo\tsessions_left\tdays_since_commit\tdeadline_in_days\tkind\tstale\tnext\tblocked_on"


def header(**fields):
    lines = ["---"] + [f"{k}: {v}" for k, v in fields.items()] + ["---", "", "# Handoff", "prose below the header"]
    return "\n".join(lines) + "\n"


def git_env(**extra):
    """An environment in which git ignores Jake's own configuration (commit
    signing, log.showSignature) and cannot be pointed at an outer repository
    by variables a git hook would set."""
    env = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.org",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.org")
    env.update(extra)
    return env


class TodayTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def make_repo(self, name, handoff_text, commit_days_ago=1, commit_time=(12, 0),
                  handoff_days_ago=0, handoff_time=(13, 0), git=True, commit=True,
                  handoff_name="HANDOFF.md"):
        """A project directory. handoff_text=None means no handoff file;
        handoff_text may be bytes to write undecodable content. git=False
        means no repository; commit=False means a repository with no commits."""
        path = os.path.join(self.root, name)
        os.makedirs(path)
        if git:
            subprocess.run(["git", "init", "-q", path], check=True, env=git_env())
        if git and commit:
            with open(os.path.join(path, "README"), "w") as fh:
                fh.write(name + "\n")
            when = datetime.datetime.combine(TODAY - datetime.timedelta(days=commit_days_ago),
                                             datetime.time(*commit_time))
            # No offset in the date, so git reads it as local time in the zone above.
            env = git_env(GIT_AUTHOR_DATE=when.strftime("%Y-%m-%dT%H:%M:%S"),
                          GIT_COMMITTER_DATE=when.strftime("%Y-%m-%dT%H:%M:%S"))
            subprocess.run(["git", "-C", path, "add", "README"], check=True, env=env)
            subprocess.run(["git", "-C", path, "commit", "-q", "-m", "init"], check=True, env=env)
        if handoff_text is not None:
            hand = os.path.join(path, handoff_name)
            mode = "wb" if isinstance(handoff_text, bytes) else "w"
            with open(hand, mode) as fh:
                fh.write(handoff_text)
            # HANDOFF.md is untracked, so its age is its modification time.
            stamp = time.mktime(datetime.datetime.combine(
                TODAY - datetime.timedelta(days=handoff_days_ago), datetime.time(*handoff_time)).timetuple())
            os.utime(hand, (stamp, stamp))
        return path

    def run_raw(self, root=None, env=None):
        return subprocess.run([sys.executable, SCRIPT, "--root", root or self.root, "--today", TODAY.isoformat()],
                              capture_output=True, text=True, env=env or git_env())

    def run_today(self, env=None):
        out = self.run_raw(env=env)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stderr, "")
        self.stdout = out.stdout
        # QUOTE_NONE: read the table exactly as an agent would see it.
        return list(csv.DictReader(io.StringIO(out.stdout), delimiter="\t", quoting=csv.QUOTE_NONE))

    def repos(self, rows):
        return [r["repo"] for r in rows]

    # --- the table itself

    def test_header_row_is_exact(self):
        self.make_repo("p", header(next="x", sessions_to_milestone=1))
        self.run_today()
        self.assertEqual(self.stdout.splitlines()[0], HEADER_ROW)

    def test_empty_root_prints_the_header_row_only(self):
        self.run_today()
        self.assertEqual(self.stdout.splitlines(), [HEADER_ROW])

    def test_missing_root_is_an_error_not_an_empty_table(self):
        missing = os.path.join(self.root, "no-such-dir")
        out = self.run_raw(root=missing)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("no-such-dir", out.stderr)
        self.assertNotIn("Traceback", out.stderr)

    # --- which projects appear

    def test_repo_with_header_appears_with_its_fields(self):
        self.make_repo("fastperm-paper", header(next="rerun the size simulation", kind="code",
                                                sessions_to_milestone=3, blocked_on="coauthor's data"))
        rows = self.run_today()
        self.assertEqual(self.repos(rows), ["fastperm-paper"])
        self.assertEqual(rows[0]["next"], "rerun the size simulation")
        self.assertEqual(rows[0]["sessions_left"], "3")
        self.assertEqual(rows[0]["kind"], "code")
        self.assertEqual(rows[0]["blocked_on"], "coauthor's data")

    def test_active_no_is_the_only_way_out(self):
        self.make_repo("old-paper", header(next="x", sessions_to_milestone=1, active="no"))
        self.make_repo("shouty", header(next="x", sessions_to_milestone=1, active="No"))
        self.make_repo("unsure", header(next="y", sessions_to_milestone=2, active="maybe"))
        self.make_repo("live-paper", header(next="z", sessions_to_milestone=3))
        self.assertEqual(self.repos(self.run_today()), ["unsure", "live-paper"])

    def test_repo_without_handoff_is_absent(self):
        self.make_repo("no-handoff", None)
        self.assertEqual(self.run_today(), [])

    def test_project_untouched_for_400_days_still_appears(self):
        # No time cutoff: Jake returns to work after a year.
        self.make_repo("sleeping", header(next="reread the draft", sessions_to_milestone=4),
                       commit_days_ago=400, handoff_days_ago=400)
        rows = self.run_today()
        self.assertEqual(self.repos(rows), ["sleeping"])
        self.assertEqual(rows[0]["days_since_commit"], "400")

    def test_handoff_in_another_case_is_found(self):
        # The Mac's file system ignores case and Linux's does not; the script
        # matches the name without regard to case so both behave the same.
        self.make_repo("lower", header(next="x", sessions_to_milestone=1), handoff_name="Handoff.md")
        self.assertEqual(self.repos(self.run_today()), ["lower"])

    def test_handoff_two_levels_down_is_ignored(self):
        # Only the immediate subdirectories of the root are projects, so the
        # script never crawls renv/, node_modules/, or nested checkouts.
        outer = os.path.join(self.root, "outer", "inner")
        os.makedirs(outer)
        with open(os.path.join(outer, "HANDOFF.md"), "w") as fh:
            fh.write(header(next="x", sessions_to_milestone=1))
        self.assertEqual(self.run_today(), [])

    def test_folder_without_git_appears_with_unknown_age(self):
        # The root itself is a repository with a commit, so an implementation
        # that runs `git -C folder log` would report the root's commit instead.
        subprocess.run(["git", "init", "-q", self.root], check=True, env=git_env())
        open(os.path.join(self.root, "root-file"), "w").close()
        subprocess.run(["git", "-C", self.root, "add", "root-file"], check=True, env=git_env())
        subprocess.run(["git", "-C", self.root, "commit", "-q", "-m", "outer"], check=True, env=git_env())
        self.make_repo("notes-only", header(next="x", sessions_to_milestone=2), git=False)
        rows = self.run_today()
        self.assertEqual(self.repos(rows), ["notes-only"])
        self.assertEqual(rows[0]["days_since_commit"], "?")

    def test_repo_with_no_commits_appears_with_unknown_age(self):
        self.make_repo("brand-new", header(next="x", sessions_to_milestone=2), commit=False)
        rows = self.run_today()
        self.assertEqual(self.repos(rows), ["brand-new"])
        self.assertEqual(rows[0]["days_since_commit"], "?")

    # --- headers that are missing or broken

    def test_handoff_without_header_shows_question_marks_and_sorts_last(self):
        # The first run shows which active projects still need a header.
        self.make_repo("needs-header", "# Handoff\n\nprose only\n")
        self.make_repo("has-header", header(next="y", kind="math", sessions_to_milestone=9))
        rows = self.run_today()
        self.assertEqual(self.repos(rows), ["has-header", "needs-header"])
        for field in ("sessions_left", "next", "kind"):
            self.assertEqual(rows[1][field], "?")

    def test_header_without_closing_line_counts_as_no_header(self):
        self.make_repo("unclosed", "---\nnext: x\nsessions_to_milestone: 1\n\n# Handoff\n")
        self.assertEqual(self.run_today()[0]["sessions_left"], "?")

    def test_line_without_colon_does_not_stop_the_run(self):
        self.make_repo("broken", "---\nthis line has no colon\nnext: fix it\nsessions_to_milestone: 2\n---\n")
        self.make_repo("fine", header(next="y", sessions_to_milestone=3))
        rows = {r["repo"]: r for r in self.run_today()}
        self.assertEqual(sorted(rows), ["broken", "fine"])
        self.assertEqual(rows["broken"]["next"], "fix it")

    def test_undecodable_handoff_does_not_stop_the_run(self):
        self.make_repo("latin1", b"---\nnext: caf\xe9\nsessions_to_milestone: 2\n---\n")
        self.make_repo("fine", header(next="y", sessions_to_milestone=3))
        self.assertEqual(sorted(self.repos(self.run_today())), ["fine", "latin1"])

    # --- parsing values

    def test_colon_inside_a_value_is_kept(self):
        self.make_repo("p", header(next="fix: the 10:30 bug", sessions_to_milestone=1))
        self.assertEqual(self.run_today()[0]["next"], "fix: the 10:30 bug")

    def test_quote_characters_inside_a_value_print_unchanged(self):
        self.make_repo("p", header(next='read "Smith 2020" first', sessions_to_milestone=1))
        self.assertEqual(self.run_today()[0]["next"], 'read "Smith 2020" first')

    def test_quotes_around_a_value_are_removed(self):
        self.make_repo("p", '---\nnext: "rerun it"\nsessions_to_milestone: \'2\'\n---\n')
        row = self.run_today()[0]
        self.assertEqual(row["next"], "rerun it")
        self.assertEqual(row["sessions_left"], "2")

    # --- order

    def test_fewest_sessions_first_as_numbers(self):
        # 10 and 2 catch an implementation that sorts the text "10" before "2".
        self.make_repo("ten", header(next="a", sessions_to_milestone=10))
        self.make_repo("unknown", header(next="b"))
        self.make_repo("two", header(next="c", sessions_to_milestone=2))
        self.make_repo("one", header(next="d", sessions_to_milestone=1))
        self.assertEqual(self.repos(self.run_today()), ["one", "two", "ten", "unknown"])

    def test_ties_go_to_the_most_recent_commit(self):
        # Names chosen so that alphabetical order would give the wrong answer.
        self.make_repo("aaa-older", header(next="a", sessions_to_milestone=2), commit_days_ago=30)
        self.make_repo("zzz-recent", header(next="b", sessions_to_milestone=2), commit_days_ago=3)
        self.assertEqual(self.repos(self.run_today()), ["zzz-recent", "aaa-older"])

    def test_last_tie_break_is_the_repo_name(self):
        # Equal sessions and no commit dates: without a final key the order
        # would follow the file system's listing, which differs by machine.
        self.make_repo("bbb", header(next="a", sessions_to_milestone=2), git=False)
        self.make_repo("aaa", header(next="b", sessions_to_milestone=2), git=False)
        self.assertEqual(self.repos(self.run_today()), ["aaa", "bbb"])

    def test_deadline_does_not_change_the_order(self):
        self.make_repo("far-from-done", header(next="a", sessions_to_milestone=6, deadline="2024-03-01"))
        self.make_repo("nearly-done", header(next="b", sessions_to_milestone=1))
        self.assertEqual(self.repos(self.run_today()), ["nearly-done", "far-from-done"])

    # --- deadlines

    def test_deadline_shows_days_remaining_across_a_leap_day(self):
        # 2024-02-27 to 2024-03-12: two days to reach 29 February, then twelve in March.
        self.make_repo("grant", header(next="a", sessions_to_milestone=2, deadline="2024-03-12"))
        self.assertEqual(self.run_today()[0]["deadline_in_days"], "14")

    def test_deadline_today_shows_zero(self):
        self.make_repo("due", header(next="a", sessions_to_milestone=2, deadline="2024-02-27"))
        self.assertEqual(self.run_today()[0]["deadline_in_days"], "0")

    def test_passed_deadline_is_blank_and_its_date_never_appears(self):
        self.make_repo("late", header(next="a", sessions_to_milestone=2, deadline="2024-02-01"))
        row = self.run_today()[0]
        self.assertEqual(row["deadline_in_days"], "")
        self.assertNotIn("2024-02-01", self.stdout)
        self.assertNotIn("overdue", self.stdout.lower())

    def test_malformed_deadline_is_blank_and_does_not_stop_the_run(self):
        self.make_repo("vague", header(next="a", sessions_to_milestone=2, deadline="soon"))
        self.assertEqual(self.run_today()[0]["deadline_in_days"], "")

    def test_no_deadline_is_blank(self):
        self.make_repo("open", header(next="a", sessions_to_milestone=2))
        self.assertEqual(self.run_today()[0]["deadline_in_days"], "")

    # --- staleness and days since the last commit

    def test_header_from_an_earlier_day_than_the_last_commit_is_stale(self):
        self.make_repo("worked-since", header(next="a", sessions_to_milestone=2),
                       commit_days_ago=2, handoff_days_ago=10)
        self.make_repo("up-to-date", header(next="b", sessions_to_milestone=3),
                       commit_days_ago=10, handoff_days_ago=2)
        rows = {r["repo"]: r for r in self.run_today()}
        self.assertEqual(rows["worked-since"]["stale"], "STALE")
        self.assertEqual(rows["up-to-date"]["stale"], "")

    def test_header_written_minutes_before_a_same_day_commit_is_current(self):
        self.make_repo("normal-session", header(next="a", sessions_to_milestone=2),
                       commit_days_ago=1, commit_time=(12, 0),
                       handoff_days_ago=1, handoff_time=(11, 55))
        self.assertEqual(self.run_today()[0]["stale"], "")

    def test_jakes_git_settings_do_not_change_the_dates(self):
        # A global setting that changes how `git log` prints dates or adds
        # signature lines must not change what the script reads.
        cfg = os.path.join(tempfile.mkdtemp(), "gitconfig")
        self.addCleanup(shutil.rmtree, os.path.dirname(cfg), True)
        with open(cfg, "w") as fh:
            fh.write("[log]\n\tdate = relative\n\tshowSignature = true\n")
        self.make_repo("p", header(next="a", sessions_to_milestone=2), commit_days_ago=1)
        self.assertEqual(self.run_today(env=git_env(GIT_CONFIG_GLOBAL=cfg))[0]["days_since_commit"], "1")

    def test_days_since_commit_counts_local_calendar_days(self):
        # 23:30 on 26 February in Chicago is 05:30 on 27 February in UTC, so
        # an implementation that counts in UTC reports 0 instead of 1.
        self.make_repo("late-night", header(next="a", sessions_to_milestone=2),
                       commit_days_ago=1, commit_time=(23, 30))
        self.assertEqual(self.run_today()[0]["days_since_commit"], "1")


if __name__ == "__main__":
    unittest.main()
