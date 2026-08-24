# Concept Map and Notation

## Purpose

This file records conventions and questions that should persist across conversations. It complements the `Revised Statistical Perspective and Learning Framework` and the `Revised Statistical Project Instructions`; it does not restate them.

Use this map to:

- keep notation stable when the same objects recur,
- prevent movement between inferential frameworks without explanation,
- preserve conceptual connections that have proved useful,
- track active questions and unresolved issues,
- and make later conversations cumulative.

This is a living index, not a transcript. A notation or connection belongs here only when it is likely to matter again.

## Recurring notation conventions

### General rules

- Define every symbol in the conversation where it first appears. This file supplies defaults, not substitutes for definitions.
- Give each symbol one role within an argument. If a source uses conflicting notation, state the local change.
- Distinguish a random object from its realization when the distinction matters. For example, write `Z` for a random assignment vector and `z` for one realized assignment.
- Qualify probability, expectation, and variance when more than one source of randomness is present. For example, `P_Z`, `E_Z`, and `Var_Z` refer to the assignment mechanism.
- State what is fixed and what is random before using a probability distribution. Potential outcomes may be fixed under randomization inference and random under a model or sampling framework.
- Use asymptotic notation only after defining the sequence: what tends to infinity, what remains fixed, and which populations, designs, or models form the sequence.

### Default symbols

| Symbol | Default meaning | Qualification |
|---|---|---|
| `N` | Number of units in a finite population | Use only when a population distinct from the observed sample exists. |
| `n` | Number of units under analysis | State whether these units are the full finite population or a sample. |
| `i` | Unit index | Usually `i = 1, ..., n`; use a second index for clusters, strata, or times. |
| `S_i` | Indicator that unit `i` is sampled | Random only under a specified sampling mechanism. |
| `Z_i` | Treatment-assignment indicator for unit `i` | `Z = (Z_1, ..., Z_n)` is random under the assignment mechanism; `z` is a realization. |
| `\mathcal{Z}` | Support of the assignment mechanism | Record restrictions such as fixed treated counts, blocks, pairs, or rerandomization. |
| `Y_i(z)` | Potential outcome for unit `i` under assignment vector `z` | The full vector `z` permits interference. Write `Y_i(a)` only when the potential outcome depends on unit `i`'s own treatment `a`. |
| `Y_i^{\mathrm{obs}}` | Observed outcome, equal to `Y_i(Z)` | This relation is the observation rule, not an assignment or sampling assumption. |
| `\tau_i` | Unit-level causal effect | Define the treatment contrast; for binary treatment without interference, `\tau_i = Y_i(1) - Y_i(0)`. |
| `\bar{\tau}` | Average causal effect over the units currently defined | Attach a subscript such as `S`, `N`, or `P` when sample, finite-population, and superpopulation effects could be confused. |
| `\theta` | Generic parameter or estimand | Replace it with a substantive symbol when one is available. |
| `\widehat{\theta}` | Estimator of `\theta` | State the source of its repeated-sampling variation. Use `\widehat{\theta}^{\mathrm{obs}}` when the realized estimate must be distinguished from the random estimator. |
| `T` | Test statistic | Write its arguments when useful, such as `T(Z, Y^{\mathrm{obs}})`. |
| `H_0`, `H_1` | Null and alternative hypotheses | State whether each hypothesis is sharp, composite, point, or set-valued. |
| `p` | p-value | Name the reference distribution and say whether randomization, sampling, or a model generates it. |
| `\alpha` | Nominal test level | Keep the nominal level distinct from the test's actual size. |
| `\Gamma` | Rosenbaum sensitivity parameter | Use only after stating the treatment-odds restriction and the observational-study design. |
| `\mathcal{U}` | Uncertainty set or class of admissible perturbations | Define what may vary and what remains fixed. |

### Probability labels

Use the following notation when several probability laws appear:

- `P_Z`, `E_Z`, and `Var_Z` for treatment assignment,
- `P_S`, `E_S`, and `Var_S` for sampling,
- `P_M`, `E_M`, and `Var_M` for an outcome or other statistical model,
- `\Pi(\cdot \mid \text{data})` for a posterior distribution,
- `P_B`, `E_B`, and `Var_B` for bootstrap resampling,
- and `P_{MC}`, `E_{MC}`, and `Var_{MC}` for Monte Carlo computation.

These labels do not imply that every analysis contains every source of randomness. Use only the labels the argument needs.

## Inferential distinctions

Keep the following objects separate. A method can address several of them, but it does not make them identical.

| Distinction | Question that fixes the distinction |
|---|---|
| Estimand vs. estimator vs. estimate | What quantity is the target, what rule estimates it, and what value did the rule produce? |
| Identification vs. estimation vs. inference | Which assumptions connect observed data to the target, how is the target estimated, and what justifies uncertainty statements? |
| Finite population vs. superpopulation | Is the target defined for these units or for a distribution from which units are viewed as draws? |
| Assignment vs. sampling vs. model randomness | Which physical or assumed process generates the reference distribution? |
| Design-based vs. model-based inference | Does validity follow from a known design, from a probability model, or from both? |
| Bayesian uncertainty vs. repeated-sampling variation | Is probability a posterior distribution conditional on observed data or a distribution over repeated samples or assignments? |
| Sharp vs. composite null | Does the null determine every missing potential outcome, or only restrict a parameter or collection of schedules? |
| Exact vs. conservative vs. asymptotic validity | Is the finite-sample rejection probability equal to, bounded by, or approaching the nominal level? |
| Conditional vs. marginal inference | What has been held fixed, and over what remaining variation is the claim averaged? |
| Nominal level vs. actual size vs. power | What error rate is promised, what is the supremum rejection probability over the null hypothesis, and what is the rejection probability under a specified alternative? |
| Weak vs. strong multiple-testing control | Is the error criterion controlled only under the global null or under every configuration of true and false nulls? |
| Robustness claim vs. perturbation class | Which departures are allowed, how large may they be, and what conclusion remains guaranteed? |
| Statistical uncertainty vs. computational error | Does uncertainty concern the inferential problem or an algorithm used to approximate its answer? |

## Recurring conceptual connections

These connections are starting points for comparison. Each one includes a condition that prevents two related ideas from being treated as interchangeable.

| Connection | Condition or boundary |
|---|---|
| Fisher randomization tests and permutation tests | A permutation distribution has a design-based interpretation only when the permutations reproduce the assignment mechanism. Imputation of missing potential outcomes also requires a sharp null or another complete causal model. |
| Test inversion and confidence sets | Inverting a family of tests yields a confidence set only with respect to the same reference distribution and error guarantee used by those tests. |
| Hodges--Lehmann estimation and test inversion | An effect estimate can be defined by the effect value that makes a test statistic central, but its interpretation depends on the causal model and the statistic being inverted. |
| Matching, stratification, and weighting | Each can be a design-stage device for constructing comparisons. Their balance properties do not by themselves identify a causal effect when hidden bias remains. |
| Sensitivity analysis and partial identification | A sensitivity parameter defines a set of admissible data-generating or assignment mechanisms. The resulting range of conclusions can be read as identification under that set only after the allowed departures are explicit. |
| Sensitivity analysis and minimax reasoning | Worst-case inference searches over an uncertainty set. The guarantee is meaningful only for the perturbations included in that set. |
| Least-favorable distributions and robust tests | A least-favorable distribution converts a composite or uncertain problem into a worst-case benchmark when it actually attains or bounds the relevant risk or error probability. |
| Likelihood ratios, Bayes factors, and e-values | All compare evidence through nonnegative ratios or averages, but they use different probability statements and guarantees. A Bayes factor is a ratio of marginal likelihoods and, for composite models, depends on parameter priors. An e-value has expectation at most one under every distribution in its null class. |
| E-values and sequential testing | The expectation bound can support optional continuation when embedded in an appropriate e-process. A single e-value does not automatically supply a valid process over time. |
| Multiple testing and decision theory | Error control constrains a repeated decision problem. The choice among familywise error, false discovery criteria, or another loss depends on which mistakes matter jointly. |
| Survey sampling and causal inference | Sampling identifies how observed units represent a population; treatment assignment identifies causal contrasts among units. One mechanism does not replace the other. |
| Randomization inference and finite-population asymptotics | Exact finite-sample results and asymptotic approximations may study the same design, but the approximation requires a stated sequence of finite populations and assignments. |
| Severity and the p-value function | In regular one-parameter problems the post-data severity curve, evaluated with the observed statistic as its threshold, and the p-value function are the same numbers. Severity then adds interpretation rather than a new quantity. The two are worth distinguishing where the selection rule or the model assumptions are themselves under scrutiny, which is the case the severity framing is built for. **Unconfirmed:** recorded 2026-08-24 from a Claude-written project-memory summary, not yet checked against Mayo and Spanos. Confirm or strike it before relying on it. |

## Active research questions

No project-specific research question has yet been promoted to this register. Do not infer one from an illustrative example or a single conversation.

Questions belonging to one paper stay with that paper. The archival-evidence
Bayes factor work keeps its open items in `~/repos/fully_specified_bf/`
(`HANDOFF.md` and the memos under `Paper/`), and they are deliberately not
copied here. This file is uploaded to more than one project, so a paper-specific
entry would follow that paper into every conversation it does not belong in.

When a question becomes active, record it in this form:

### Short question title

- **Question:** One sentence that can be true or false.
- **Why it matters:** The statistical problem the answer would solve.
- **Target:** The estimand, hypothesis, decision, or guarantee under study.
- **Source of randomness:** Assignment, sampling, model, posterior, computation, or a stated combination.
- **Current assumptions:** Only the assumptions presently required.
- **Current status:** `exploratory`, `conjectured`, `partly derived`, `proved`, `disproved`, or `parked`.
- **Next check:** The smallest derivation, counterexample, simulation, or literature search that would change the status.
- **Last updated:** `YYYY-MM-DD` and the conversation title.

## Unresolved issues

No project-specific unresolved issue has yet been recorded.

Use this section for a definite gap that persists across conversations, not for every open-ended topic. Each entry should state:

- the disputed or missing claim,
- why the gap affects an inference,
- what has already been established,
- what evidence or argument would resolve it,
- and whether work is `open`, `blocked`, `resolved`, or `abandoned`.

When an issue is resolved, keep a one-sentence resolution and move any durable result to the relevant conceptual connection or notation convention.

## Updating this map

Use the following lightweight protocol:

1. **Identify a durable change.** Update the map only when a conversation establishes a recurring notation choice, a reusable conceptual connection, an active research question, or a genuine unresolved issue.
2. **Separate established from tentative material.** Label definitions, derivations, conjectures, simulations, and literature-based claims according to the evidence that supports them.
3. **Make the smallest edit.** Revise an existing entry when possible. Do not paste conversation summaries into this file.
4. **Record provenance.** Add the date and conversation title to active questions and unresolved issues. Add a citation only when the entry depends on a specific external result.
5. **Resolve conflicts explicitly.** If later work changes a convention or overturns a claim, replace the old entry and note the reason. Do not retain two silent defaults.
6. **Review occasionally.** After several substantive conversations, remove duplicate entries, shorten resolved issues, and check that every symbol still has one default role.

At the end of a conversation, a useful update should fit in one to three entries. If nothing durable changed, leave this file unchanged.
