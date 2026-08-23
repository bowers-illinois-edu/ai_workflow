# Block 4 of 4: Coding instructions (project)

Make a project for code work and paste the text below the line into its custom
instructions. Block 1 already carries the short version --- explain the
statistical idea, tests before the code, comment why --- so a one-off coding
question in ordinary chat is covered without this block. This block is for the
sessions where something is actually being built.

The app cannot read files on my machine, so the parts of the Claude Code rules
that assume a working tree are restated here as things to ask me for.

If the field rejects it for length, cut the R-package paragraph first.

Synced against CLAUDE_CODING.md at commit a500d5f (2026-08-23).

-------------------------------------------------------------------------------

Before writing code, find out what the code is for. Code that supports a paper
has a point --- an estimand, a hypothesis, a figure, a claim I am trying to
check --- and the right implementation depends on that point. If I have not told
you, ask. If I paste a function without its surroundings, ask for the files you
need rather than guessing at them: for an R package that usually means the rest
of R/, the tests, NAMESPACE and DESCRIPTION, and any vignette that touches the
same functionality.

Write the tests before the code, and before any refactor. A test should encode
the statistical principle that justifies the code and the substantive point the
code exists to make. If I am writing code to square numbers, the test that
matters is that it squares numbers, not that numeric input yields numeric
output. Do not delete a failing test to make a suite pass. Fix the code, or ask
me. If a failure cannot be resolved quickly, skipping the test is allowed as
long as you tell me it is now an open task. Readable, maintainable tests beat
comprehensive coverage. Show me the tests and stop for my review before you
write the implementation.

Prefer boring code over clever code. In R this is not an argument for for()
loops: vectorized code is usually both faster and clearer, because a loop needs
extra code to preallocate and fill the objects it writes into.

Comment why a section or a line is there, more than what it does.

Group functions by conceptual purpose, one file per coherent unit. Tell me
before a file grows past roughly 300 lines. When a new function is conceptually
distinct from what is already in a file --- a different mechanism, a different
external dependency, a different layer of abstraction --- start a new file
instead of appending.

Write code that can be saved in files and rerun later by other researchers on
other machines. I am willing to require Unix or Linux. Some code belongs in the
project's git repository because replication depends on it and some does not, so
say which you think it is when it is not obvious.

For R packages: documentation is roxygen2, so a change to documentation means
running devtools::document(); devtools::check() should pass before the work
counts as done; adding an exported function means bumping the patch version in
DESCRIPTION.

When a design decision comes up that we have not already settled, stop and ask
me rather than picking one and moving on.
