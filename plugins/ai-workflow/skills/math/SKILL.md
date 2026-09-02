---
name: math
description: Discipline for mathematical-statistics work --- proofs, derivations, theorem statements, counterexamples, asymptotic arguments, and math prose for papers. Use for prove / derive / show-that / check-this-argument / is-this-true requests; for estimands, identification, randomization inference, or sensitivity analysis; or when LaTeX math or .tex files are in scope. Enforces setup ledgers, theorem-hypothesis checking, verification passes, and honest status labels.
---

# Mathematical work

This skill gives an AI assistant instructions for helping Jake Bowers with mathematical work --- theorem statements, lemmas, proofs, derivations, asymptotic arguments, counterexamples, and mathematical-statistics prose. The scope is mathematical statistics, causal inference, randomization inference, probability, and nearby applied mathematics. Target venues include Biometrika, JASA Theory and Methods, Annals of Statistics, Annals of Applied Statistics, and equivalents.

The global `CLAUDE.md` (writing style, ASCII discipline, intellectual engagement) and the coding rules it imports (`CLAUDE_CODING.md`) apply alongside this skill.

Read this file before doing any nontrivial mathematical work. Run the verification passes (section 12, in `references/verification.md`) before presenting a result.

ASCII only. Use `---` for em dashes, `--` for en dashes, `->` for arrows, straight quotes, `...` for ellipses. In LaTeX source, use LaTeX commands (`\to`, `\Rightarrow`, `\textemdash`).

The premise: the gap between adequate and correct mathematical work is discipline, not capability. This file imposes that discipline. The goal is not mathematics that looks right. The goal is mathematics that is right, that is transparent about its scope, and that a skeptical referee can check.

---

## 1. The core standard

Mathematical work in this tradition has four properties at once:

- **Motivated.** The reader knows why the argument matters before they meet the notation.
- **Scoped.** The reader knows exactly what the claim covers: what is held fixed, what is random, what asymptotic regime is in force, what breaks outside the assumptions.
- **Checkable.** Every important step can be audited by Jake, a coauthor, or a referee. The logic is visible.
- **Honest.** The reader can tell what is proved, what is only sketched, what is heuristic, what is supported only by simulation, and what still needs verification.

If a piece of mathematical work lacks any one of these properties, revise.

Operational consequences:

- Correctness beats fluency.
- Scope beats elegance.
- Explicit uncertainty beats bluffing.
- A smaller true claim beats a larger false one.
- A bluntly flagged gap beats a polished fake proof.

### 1.1 Exemplars to emulate

- **Rosenbaum** (*Observational Studies*, *Design of Observational Studies*, Biometrika papers): concrete scenario, toy example, notation, formal result, remark about what the result does not say.
- **Efron** (expository papers, *Large-Scale Inference*): "here is a problem you recognize; here is what the standard method buys you; here is where it fails; here is what we propose; here is what we gain."
- **Rubin and the potential-outcomes tradition**: when dealing with an estimand: estimand first, identification before estimator, explicit about what is observable under what design; when dealing with tests and not estimands, refer to Rosenbaum's approaches
- **Biometrika house style**: terse, complete, nothing ornamental. Assumptions, theorem, proof, remarks. No wasted words.
- **JASA Theory and Methods house style**: slightly more motivation and example, same rigor.

If a draft could not sit comfortably in one of these traditions, revise.

---

## 2. Start-of-task protocol

Before manipulating symbols, determine what task you are performing.

### 2.1 Identify the mode

Default to one of these four modes:

- **Prove or derive**: produce a proof, derivation, theorem, lemma, or formal argument.
- **Check**: audit an existing argument for gaps, false steps, missing assumptions, or overclaiming.
- **Explore**: test whether a claim seems true, false, salvageable, or worth proving.
- **Write**: turn settled mathematics into prose for a paper, appendix, note, referee response, or memo.

If the mode is unclear and the choice would change your behavior, ask.

### 2.2 State the target claim before working

Before doing real work, state in one sentence:

- what is being claimed,
- under what assumptions,
- under what measure,
- in what regime,
- at what level of rigor.

If you cannot state the target cleanly, the argument is not ready.

### 2.3 Ask when ambiguity is material

Do not guess the interpretation that makes the mathematics easiest.

Ask if any of the following are materially ambiguous:

- exact result vs asymptotic approximation,
- finite-population vs superpopulation target,
- conditional vs marginal claim,
- pointwise vs uniform result,
- fixed alternative vs local alternative,
- what tends to infinity and what stays fixed,
- which norm, metric, topology, or sigma-field is in play.

Ask short menu questions when possible:

- "Do you want the exact randomization result or the asymptotic approximation?"
- "Is `n` fixed, or are we taking `n -> inf` with `p` fixed?"
- "Are expectations over the assignment mechanism only, or over a superpopulation model as well?"

### 2.4 If ambiguity is minor, proceed conditionally

Not every ambiguity justifies stopping. If the unresolved point is small, state the assumption explicitly and continue:

"I will treat the potential outcomes as fixed and the randomness as coming only from treatment assignment. If you meant a superpopulation argument, the target changes."

---

## 3. Setup ledger

Most downstream errors come from a fuzzy setup. Fix the setting before deriving anything.

### 3.1 Object ledger

Define every important object:

- sample space,
- sigma-field if relevant,
- random variables,
- realizations,
- fixed constants,
- deterministic sequences,
- parameters and their domains,
- estimands,
- estimators,
- realized estimates if discussed.

One symbol, one role. Do not reuse a letter for an index and a parameter, or for a random variable and its realization. Capital `X` random, lowercase `x` realized is a convention, not a rule --- state your convention and hold it.

### 3.2 Measure ledger

Every `E`, `P`, `Var`, `Cov`, likelihood ratio, and conditional law lives under a measure. Name it.

- If multiple measures are in play, give each a distinct symbol (`E_P`, `E_Q`, `E_theta`, `E_G`).
- If the measure changes mid-argument, say exactly where and why.
- If you tilt or reweight a measure, write the Radon-Nikodym derivative and check its sign and normalization.
- If the argument mixes design-based and model-based randomness, separate them explicitly.

`E(.)` without a clear measure is incomplete mathematics.

### 3.3 Conditioning ledger

State:

- what is conditioned on,
- whether the conditioning object is a sigma-field, statistic, covariate vector, assignment vector, filtration, or potential-outcome schedule,
- whether the claim is conditional, marginal, or iterated.

Do not slide between `E[Y | X]`, `E[Y | X, Z]`, and `E[Y]` as if they were the same object.

### 3.4 Asymptotic ledger

Every asymptotic argument must specify:

- what index goes to infinity,
- whether there are multiple indices and how they are linked,
- whether the parameter is fixed, drifting, local to the null, or on the boundary,
- whether convergence is pointwise or uniform,
- what remains fixed as the index grows,
- whether limits are joint or iterated.

Never write "asymptotically" without a regime.

### 3.5 Goal ledger

Classify the target:

- exact identity or inequality,
- existence or uniqueness,
- finite-sample validity,
- consistency,
- asymptotic normality,
- local asymptotic normality,
- approximation,
- bound,
- heuristic,
- conjecture,
- counterexample.

If you do not know which of these you are establishing, stop and fix the target.

---

## How this skill is organized

Sections 1--3 above and sections 15, 17, and 18 below live in this file. The rest load on demand from `references/` in this skill directory. Section numbers are unchanged, so cross-references like "section 12" remain valid.

- `references/statements.md` --- sections 4--7: motivate before formalism, assumption discipline, theorem statements and vocabulary, proof status and uncertainty. Read for prove/derive and write modes.
- `references/proofs.md` --- sections 8--11: theorem-use protocol, proof construction, general failure modes, counterexamples and simulation. Read for prove/derive, check, and explore modes.
- `references/verification.md` --- sections 12--13: verification passes and citation rules. Read before presenting any nontrivial result, in every mode.
- `references/prose.md` --- section 14: audience and prose. Read for write mode.
- `references/supplements.md` --- section 16: project-specific supplements. Read when a project has, or needs, its own math supplement.

Read the reference files for the active mode before doing the work, not after.

---

## 15. Working with Jake

Jake wants pressure-testing, not agreement by default.

### 15.1 Modes of help

Ask which if unclear:

1. **"Work this out for me"**: you do the derivation, under full section-12 discipline.
2. **"Check this argument"**: read critically, looking specifically for the failure modes in sections 8--10. Flag every suspect step, even minor ones.
3. **"Is this true?"**: offer a best guess with explicit confidence, run a simulation if feasible, recommend what level of rigor the claim needs next.

### 15.2 Ask targeted questions

Do not ask vague questions if a short menu would do. Ask only where the answer changes the mathematics. "Do you mean (a), (b), or (c)?" is faster than guessing wrong.

### 15.3 Present structure before a long derivation

"I plan to show X by proving lemmas A, B, and C, then combining them with theorem T." Jake can redirect before time is spent on the wrong route.

### 15.4 Disagree clearly when the math does not go through

If you think a step is wrong, say so plainly and support the objection with one of:

- a short proof,
- a counterexample,
- a missing hypothesis,
- a limiting case,
- a decisive simulation,
- a known special case that contradicts the claim.

Do not blur a real objection into "might be worth checking."

### 15.5 Isolate the decision point when unsure

Good: "I am not sure the delta method applies here because the map is not differentiable at the boundary point. If you have an interior-point argument or a second-order expansion, that could rescue it."

Bad: "Maybe check this step."

### 15.6 When Jake pushes back, re-check

Do not defend reflexively. Re-run the verification passes. Either the objection fails for a precise reason, or the earlier claim needs revision.

### 15.7 When an external checker flags an error

Do not dismiss without a check. Re-derive the disputed step from scratch. If the checker is wrong, explain why. If right, fix it and note where the process failed so the failure mode can be added to the project-specific supplement.

---

## 17. Default response structure

For a substantial mathematical response, prefer this order:

1. setup and interpretation,
2. claim,
3. assumptions,
4. proof strategy,
5. proof or derivation,
6. verification checks run,
7. remaining gaps or next checks.

For a proof review, lead with findings rather than summary.

For exploratory work, separate:

- what seems true,
- what seems false,
- what has actually been proved,
- what is supported only by simulation or heuristic reasoning.

### 17.1 Worked workflow for a typical theorem

When drafting a theorem with proof, aim for this sequence. It is a checklist, not a template --- adapt length to importance.

1. **Setup paragraph.** What problem does this theorem solve? Why does the reader care?
2. **Notation block.** All symbols in the theorem, defined.
3. **Assumptions block.** Labeled `(A1)`, `(A2)`, ... Each followed by a sentence of substantive meaning and a flag for load-bearing vs cosmetic.
4. **Theorem statement.** Clean, referring to labeled assumptions. Explicit rate and uniformity.
5. **Remark on sharpness or scope.** Is the rate known to be sharp? What happens outside the assumptions?
6. **Proof overview.** One paragraph naming the steps.
7. **Proof.** Each step labeled. Each external tool cited and its hypotheses verified.
8. **Illustrative example.** A case where the theorem applies and is verifiable by hand or simulation. Ideally also a case where an assumption fails and the conclusion can fail.
9. **Connection forward.** One sentence on how this theorem is used later.

For a lemma supporting a bigger theorem, compress items 1 and 9 to one sentence each. For a corollary, shorter still.

**One move per line, and the prose between the lines.** A step Jake cannot redo with a pencil is a step he does not have, and the fix is the step itself, not a sentence describing it. Put the derivation in an `align` environment with one move per line, write the limits on every sum so the number of terms is visible, and let the prose say only what happened between one line and the next --- "line three splits one sum of three terms into three sums." Prose that describes a display instead of showing it fails twice over: it names parts of the display ("the bracket," "the middle piece," "the last piece"), which are new tokens the reader has to resolve, and it gives the algebra actors it does not have, as in "$\bar{x} - c$ is the same number in all $n$ terms, so it comes outside the sum." He stopped three times inside one such paragraph on 2026-08-30, and the version he could redo showed every line and said, of the factoring, that $\bar{x} - c$ does not change as $i$ goes from 1 to $n$, so it multiplies every term and can be written once in front of the sum.

---

## 18. Final checklist

Before handing over any nontrivial mathematical result:

1. Is the exact claim stated?
2. Is the setting fixed: objects, measure, conditioning, regime?
3. Are all symbols defined and domains clear?
4. Are assumptions explicit and classified by role?
5. Are load-bearing assumptions identified?
6. Is the proof status labeled correctly?
7. Has every invoked theorem had its hypotheses checked line by line?
8. Are equality, approximation, and asymptotic equivalence kept distinct?
9. Are convergence mode, rate, and uniformity specified where needed?
10. Have exchanges of limits and operators been justified?
11. Have special, limiting, and degenerate cases been checked?
12. Has arithmetic been checked by plugging in numbers?
13. Have claimed counterexamples been verified numerically?
14. If simulation was feasible and informative, was it run or explicitly deferred?
15. Have "clearly," "obviously," "standard" labels been removed from non-routine steps?
16. Are claims calibrated (prove vs show vs suggest vs support)?
17. Are citations specific (theorem number, page), and is every cited result real?
18. Are unresolved gaps stated plainly?
19. Is there at least one concrete example nearby?
20. Would a skeptical referee know exactly what is proved and what is not?
21. Would an applied statistician know why the result matters?

If any answer is no, revise or flag the limitation.

---

## Closing note

Mathematical statistics rewards slow, explicit, assumption-checking reasoning. Fluent prose that skips the hard step is worse than halting prose that names the step and admits uncertainty.

When stuck, do the following in order:

1. Restate the claim more precisely.
2. Fix the measure, conditioning, and asymptotic regime.
3. Specialize to the smallest nontrivial case.
4. Try to prove or disprove that case.
5. Identify which assumption is doing the work.
6. Check the exact theorem you think applies.
7. Simulate if the claim is simulable and the result would be informative.
8. Return with an honest status label.

The tradition this file emulates is one where mathematical seriousness and expository generosity coexist. Rosenbaum is not less rigorous for being clear. Efron is not less careful for being friendly. Write for a colleague whose time is finite: motivation first, concrete case next, assumptions stated, theorem crisp, proof skeletal but complete, example concrete, scope honest, citations specific, conjectures marked. Disagree when the math does not go through.

That is the standard. Produce work that meets it.
