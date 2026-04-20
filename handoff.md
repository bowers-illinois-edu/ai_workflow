# HANDOFF.md

Session date: 2026-04-19. Working directory: `/Users/jwbowers/repos/ai_workflow`.

## Session goal

Synthesize two draft instruction files (`AI_MATH.md` and the old `CLAUDE_MATH.md`) into a single general-purpose file for instructing an AI assistant on mathematical-statistics work: proofs, derivations, theorem statements, counterexamples, and mathematical prose. Add infrastructure for per-project supplements.

## Key decisions made

1. **Do not use `AI_MATH.md` alone.** It has the better protocol structure (modes, ledgers, theorem-use protocol, when-stuck algorithm) but loses substantive guidance and stylistic anchors that the old `CLAUDE_MATH.md` provided. Synthesis was the right move.

2. **Backbone from `AI_MATH.md`, substance from `CLAUDE_MATH.md`.** The new file keeps `AI_MATH.md`'s organizing structure (start-of-task modes, setup ledger, theorem-use protocol, verification passes, final checklist, when-stuck closing algorithm) and folds in `CLAUDE_MATH.md`'s exemplars (Rosenbaum, Efron, Rubin, Biometrika, JASA T&M), richer failure-mode content, necessary-vs-sufficient discipline, probability-vocabulary gradations, and the worked-workflow-for-a-theorem template.

3. **General-purpose, not specialized.** Removed the saddlepoint / Edgeworth / importance-sampling / tilting material from the main body per the user's instruction. Kept a short general-purpose danger-zones list in section 10.7 (likelihood, delta method, M-estimation, empirical processes, CLTs, randomization inference) because those touch most projects. Pushed subfield-specific content to the new section 16 on project supplements.

4. **No traffic-light jargon in user-visible output.** `AI_MATH.md` proposed green/yellow/red confidence tiers. The user does not want that vocabulary exposed. Section 7.2 of the new file says: track confidence internally, flag uncertainty in plain English.

5. **New section 16: project-specific supplements.** The user asked how to specialize the general instructions for individual projects (e.g., `~/repos/fastperm-paper` needs saddlepoint material; `~/repos/manytests-paper` needs different material). Solution: a `CLAUDE_MATH.md` in each project root that extends the general file. Section 16 covers when to create one, where to put it, what it contains, how to invoke it, and includes a minimal template. It also instructs the assistant to add observed failure modes to the supplement as they occur, so the supplement accumulates project memory.

6. **Filename convention.** Two files share the name `CLAUDE_MATH.md`: the general one in `~/repos/ai_workflow/`, and a per-project one in each project root. Paths disambiguate them. Import syntax makes the distinction visible: `@/Users/jwbowers/repos/ai_workflow/CLAUDE_MATH.md` vs `@./CLAUDE_MATH.md`.

7. **User edited section 1.1 bullet on Rubin.** After the first draft, the user modified the Rubin bullet to read: "when dealing with an estimand: estimand first, identification before estimator, explicit about what is observable under what design; when dealing with tests and not estimands, refer to Rosenbaum's approaches." This is a substantive refinement --- estimand-first is the Rubin frame, but test-based inference (especially randomization-based) belongs to Rosenbaum. Preserve this in future edits.

## Files changed

- **`CLAUDE_MATH.md`** (new content, same filename): the synthesized general-purpose instruction file. Created as `CLAUDE_MATH_NEW.md`, then renamed to overwrite the old `CLAUDE_MATH.md`. About 600 lines. 18 numbered sections plus exemplars block and closing note.
- **`README_MATH.md`** (new file): explains how to use `CLAUDE_MATH.md` with Claude Code in a specific project. Covers three invocation options (auto-import via `@`, explicit per-session invocation, hybrid) and recommends the hybrid. Includes the boilerplate sentence for starting a math session.
- **`HANDOFF.md`** (this file).

## Files not touched

- `AI_MATH.md` --- left in place. Was the primary source for the new file's skeleton.
- `AI_MATH_A.md`, `AI_MATH_B.md` --- user said to leave them; they will delete.
- `CLAUDE.md` (user global and project) --- writing-style file; unchanged.
- `CLAUDE_CODING.md` --- coding file; unchanged.
- `CLAUDE_REVIEW-RESPONSE.md`, handoff skills, deck-generation prompt, etc. --- unrelated to this session.

## Current state of the trio

The user's instruction trio is now:

- `CLAUDE.md` --- writing.
- `CLAUDE_CODING.md` --- coding (R).
- `CLAUDE_MATH.md` --- mathematical statistics.

`README_MATH.md` documents how to wire `CLAUDE_MATH.md` into specific project repos.

## Open questions / potential next steps

1. **Section 10.7 (general danger zones) --- keep or cut?** I flagged this to the user as a potentially cuttable section: it lists general mathematical-statistics danger zones (likelihood, delta method, M-estimation, empirical processes, CLTs, randomization inference) in the general file. An alternative is to strip it entirely and put each danger zone only in the relevant project's supplement. The user did not respond; the section remains. Ask before removing.

2. **Section 1.1 exemplars --- keep or cut?** I also flagged that the named exemplars (Rosenbaum, Efron, Rubin, Biometrika, JASA T&M) may feel parochial if the file is shared with collaborators outside the user's tradition. The user did not respond but did edit the Rubin bullet, suggesting they want to keep exemplars. Keep unless asked.

3. **Should similar README files exist for `CLAUDE.md` and `CLAUDE_CODING.md`?** `README_MATH.md` only covers the math file. If the user wants consistent invocation infrastructure across the trio, analogous READMEs (or a single combined one) might make sense.

4. **First-use validation.** The new `CLAUDE_MATH.md` has not been used in an actual math session yet. Once the user exercises it on a real project (fastperm, manytests, or similar), friction points will surface. Expect minor edits at that point.

5. **Project supplements.** No project supplements have been created yet. When the user starts the next math session in `~/repos/fastperm-paper` or `~/repos/manytests-paper`, step one is creating `CLAUDE_MATH.md` in the project root using the template in section 16.6 of the general file. For fastperm, the supplement would include saddlepoint/Edgeworth/tilting material that was deliberately excluded from the general file.

## Important context to preserve

- **User profile.** Jake Bowers, applied statistician, political methodology. Causal inference, randomization inference, hypothesis testing, research design. Faculty at UIUC. Prefers R for code, ASCII for plain text, `---` for em dashes, explicit uncertainty, stress-testing over agreement by default.
- **Style anchors.** The file is written in the tradition of Rosenbaum, Efron, Rubin, and Biometrika/JASA T&M house style. That tradition is cited directly in section 1.1.
- **Design principle.** The file imposes discipline: the gap between adequate and correct mathematical work is discipline, not capability. The goal is mathematics that is right, not mathematics that looks right.
- **Intended invocation.** Per `README_MATH.md`, the user leans toward the hybrid option: global `CLAUDE.md` auto-loaded; `CLAUDE_MATH.md` loaded explicitly at the start of a math session with a one-sentence invocation that also names the mode (Prove / Check / Explore / Write).
- **User wants plain-English uncertainty, not jargon.** If a step is shaky, the assistant should say so in readable prose, not "this step is yellow."

## What is done

- Two source files read and compared.
- User given a written comparison and recommendation (synthesize, don't use `AI_MATH.md` alone).
- New synthesized `CLAUDE_MATH.md` written (~600 lines, 18 sections).
- Old `CLAUDE_MATH.md` overwritten with the new file (rename of `CLAUDE_MATH_NEW.md`).
- User edited section 1.1 Rubin bullet; edit preserved.
- `README_MATH.md` written explaining project-level invocation patterns.
- Three invocation options documented; hybrid recommended.

## What remains

- Exercise the new file on a real math session and record friction.
- Create the first per-project `CLAUDE_MATH.md` (likely `~/repos/fastperm-paper` given that saddlepoint content was carved out of the general file explicitly for this supplement).
- Consider whether to commit the new files to git. Git status at session start showed `CLAUDE_MATH_NEW.md`, `AI_MATH_A.md`, `AI_MATH_B.md`, and related files as untracked; the rename overwrote a tracked `CLAUDE_MATH.md`, so that file is now modified in the working tree, and `README_MATH.md` plus `HANDOFF.md` are untracked. User has not asked to commit --- do not commit without explicit instruction.
- Decide on the open questions above (sections 10.7 and 1.1, and whether parallel READMEs for the other CLAUDE files are wanted).
