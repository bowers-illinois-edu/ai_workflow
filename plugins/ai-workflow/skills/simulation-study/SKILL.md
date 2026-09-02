---
name: simulation-study
description: Design, run, and report Monte Carlo simulation studies of operating characteristics --- bias, variance/MSE, size, power, coverage, interval length --- for estimators and tests. Use for "simulation study," "operating characteristics," "check size / power / coverage," "Monte Carlo evidence," or when planning or auditing the simulation section of a methods paper. Enforces a design ledger before code, seed and parallel-RNG discipline, Monte Carlo uncertainty on every reported number, and honest scope claims.
---

# Simulation studies

This skill gives an AI assistant instructions for designing, implementing,
and reporting Monte Carlo simulation studies for Jake Bowers. It extends the
math skill's section 11.2 --- simulation can falsify, calibrate, and
prioritize; it does not prove theorems --- from quick diagnostics to full
studies destined for a paper. `CLAUDE_CODING.md` governs the code
(tests first, Makefile discipline, replication on other machines); the
global `CLAUDE.md` governs the prose that reports the results.

The premise: a simulation study is an experiment run on a computer. It has
an estimand (the operating characteristic), a design (factors, levels,
replications), and uncertainty (Monte Carlo error). Everything Jake demands
of a field experiment --- the target stated before the analysis, the design
chosen before the results are seen, uncertainty reported --- applies.

## 1. Design ledger before code

Write these down and confirm them with Jake before implementing. A fuzzy
ledger here is the simulation analog of the math skill's fuzzy setup.

1. **Procedures.** The estimator or test under study, and every comparator,
   each with the reason it is in the study. A comparator no reader would ask
   about costs cells; a comparator every referee will ask about cannot be
   missing.
2. **Criteria, defined as functionals.** Bias and variance/MSE of what,
   over what distribution; size as the rejection rate under which null at
   which alpha; power against which named alternatives; coverage of which
   parameter by which interval, plus interval length. Write each as a
   quantity the simulation estimates, because that is what it is.
3. **Data-generating processes, tied to assumptions.** At least one DGP
   satisfies the procedure's assumptions (the calibration case --- if the
   procedure fails here, stop and find out why). Add one DGP per assumption
   whose violation the paper discusses: the study earns the right to say
   "robust to X" only by simulating a violation of X. For design-based
   work, hold potential outcomes fixed and rerandomize assignment --- the
   randomness must come from the mechanism the inference claims it comes
   from (math skill 10.4).
4. **Factors and levels.** Sample size, effect size, dependence or ICC,
   outcome distributions, and whatever else varies --- as an explicit
   factorial table. Cells omitted from a full factorial are named and the
   reason given; a missing cell a reader would expect reads as a hidden
   failure.
5. **Replications, justified by Monte Carlo error.** Choose the target
   precision first, then derive the number of replications B. For a
   rejection or coverage proportion p, the Monte Carlo standard error is
   sqrt(p(1-p)/B): checking size at alpha = 0.05 with B = 10,000 gives
   MCSE about 0.002, so an estimated size of 0.056 is distinguishable from
   nominal and one of 0.051 is not. State the arithmetic in the ledger.

## 2. Implementation discipline

- **Tests before scale** (`CLAUDE_CODING.md` applied here): before the full
  grid runs, a unit test shows the harness recovers a known answer --- a
  case with a closed form, or the calibration DGP at small B --- within
  Monte Carlo error. A harness bug found after a cluster run is the
  expensive version of the same bug found in a test.
- **Seeds and parallel RNG.** One master seed recorded in the script;
  parallel streams via a parallel-safe generator (in R,
  `RNGkind("L'Ecuyer-CMRG")` with `parallel`/`future`, or per-cell seeds
  derived reproducibly from the master). A rerun on the same seed
  reproduces the results file byte-for-byte where the platform allows;
  record package versions (renv lockfile) either way.
- **Store replication-level results,** tidy and long: one row per
  replication x cell x procedure, with the seed or stream id. Summaries
  (means, rejection rates, coverage) are recomputed from this file, never
  hand-maintained. Summaries without the replication-level file cannot
  answer the referee who asks for a different summary.
- **Chunk and cache.** One results file per cell or per script (the
  pattern in Jake's existing projects: each sim script writes its own
  `.rda`), orchestrated by the Makefile, so a crash costs one chunk and an
  edited DGP invalidates only its own targets.
- **Numeric claims trace to generators.** Any simulated number quoted in
  the paper is written by code into a macros file or table, not typed by
  hand (the `write_paper_macros.R` pattern: generated, then
  regression-tested against the `.rda` sources).

## 3. Analysis and reporting

- **Monte Carlo uncertainty appears next to every simulated number.** A
  rejection rate without its MCSE (or a coverage plot without its error
  band) claims more precision than the study has. This is not optional
  polish; it is the difference between reporting an estimate and reporting
  a number.
- **Plots over tables, reference lines always.** Size and coverage plots
  carry the nominal level as a reference line and the MC error band around
  it; power curves run over effect size with one panel or line per factor
  level. A table is for the handful of numbers the text discusses.
- **Report every cell run.** A cell dropped from the paper needs a stated
  reason in the text or the supplement. Selective reporting of favorable
  cells is the simulation version of the unreported specification search.
- **Verbs at simulation strength** (math skill 6.3): simulations "suggest,"
  "are consistent with," "show no violations across the designs studied";
  they do not "prove" or "establish." Scope the conclusion to the DGPs and
  ranges actually simulated, and name the untested regimes --- "we did not
  vary cluster size" is a sentence that belongs in the paper, not a fact to
  hope nobody notices.

## 4. Verification passes

Run before presenting results; report which were run and what they found.

1. **Null calibration.** In the assumptions-satisfied cell, estimated size
   is within MC error of alpha, and coverage of the true parameter is
   within MC error of nominal. Failure here is a harness bug or a broken
   procedure --- find out which before running anything else.
2. **Closed-form recovery.** Where a theoretical value exists (a known
   variance, a normal-theory power), the simulation recovers it within MC
   error.
3. **Invariance checks.** Transformations that should not change results
   (relabeling arms, permuting block labels, shifting outcomes when the
   statistic is shift-invariant) do not change them.
4. **Seed-stability spot check.** One or two cells rerun under a different
   master seed move within MC error.
5. **Monotonicity sanity.** Power rises with effect size and with n; where
   it does not, either the procedure genuinely behaves that way (worth a
   remark in the paper) or the harness is wrong.

## 5. Reporting rule

Do not say "simulations confirm the method works." Say what ran and what
came out: the grid ("14 scenarios x 7 methods"), B per cell, the seed
policy, the versions, which verification passes ran, and the findings with
their MC uncertainty. Good: "Size in the calibration cell: 0.049 (MCSE
0.002, B = 10,000). Under the t(3) outcome DGP the normal-theory interval
undercovers: 0.918 (MCSE 0.003)." Bad: "The method performs well across a
range of settings."

## 6. Final checklist

1. Ledger written and confirmed before code: procedures, criteria as
   functionals, DGPs tied to assumptions, factor table, B derived from a
   stated precision target?
2. Calibration DGP included and passed?
3. Harness unit-tested against a known answer before the full run?
4. Master seed, parallel-RNG policy, and package versions recorded?
5. Replication-level results stored tidy; all summaries recomputable?
6. Every reported number carries MC uncertainty?
7. Every cell accounted for --- reported or its omission explained?
8. Conclusions scoped to the simulated regimes, untested regimes named?
9. Verbs at simulation strength throughout?
