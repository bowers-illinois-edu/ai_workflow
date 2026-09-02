# Math skill reference --- section 16: project-specific supplements

Part of the `math` skill; read `SKILL.md` first. Section numbers continue the skill's single sequence.

## 16. Project-specific supplements

This file is deliberately general. Each project involves specialized techniques, literatures, conventions, and traps that do not belong in the general file. Maintain a per-project supplement that extends this one.

### 16.1 When to create a supplement

Create a project-specific supplement when the project involves:

- a subfield with its own named theorems and load-bearing conditions (for example: saddlepoint or Edgeworth expansions, large-deviation theory, importance sampling and tilting, high-dimensional asymptotics, functional data, semiparametric efficiency theory, martingale CLTs, sensitivity analysis in observational studies);
- notational conventions specific to the project (symbol choices, estimand definitions);
- a specific literature the paper is in conversation with, whose results will be invoked or extended;
- recurrent failure modes that came up during the project and should not come up again.

### 16.2 Location and naming

Put the supplement in the project repository root as `CLAUDE_MATH.md` (or whatever filename Jake prefers for that project). It lives next to the project's own `CLAUDE.md` if one exists.

### 16.3 What a supplement should contain

A supplement is an overlay, not a replacement. Do not restate the general principles. Include:

1. **Project scope**: one paragraph on what the project is and what kinds of mathematical work it involves.
2. **Notation and conventions**: symbol definitions, hat/tilde/bar conventions, estimand notation, measure notation specific to the project.
3. **Key theorems and their exact statements**: the theorems the paper will invoke repeatedly, with precise hypotheses and canonical references. Include any adaptations or corollaries the paper relies on.
4. **Subfield-specific danger zones**: for the techniques in use, what must be checked every time. Examples:
   - *saddlepoint / Edgeworth*: domain where the CGF is finite, lattice vs non-lattice, uniformity range of the remainder, absolute vs relative error, moderate vs large deviation regime;
   - *importance sampling / tilting*: proposal dominance for unbiasedness, `L^2` likelihood ratio for finite variance, sign and normalization of the Radon-Nikodym derivative;
   - *randomization inference*: finite-population vs superpopulation target, exact randomization distribution vs asymptotic approximation, conditioning on strata sizes vs on the full potential-outcome schedule;
   - *high-dimensional*: how `p` and `n` are linked, sparsity conditions, restricted eigenvalue conditions, rate consequences.
5. **Simulation conventions**: standard designs, seeds, sample sizes used for diagnostic simulation in this project.
6. **Running list of project-specific failure modes**: errors that came up once should be recorded so they do not come up again.
7. **Key references**: the 10--20 papers and books the project draws on most heavily, with brief annotations on what each is used for.

### 16.4 How to invoke

The `math` skill loads on its own triggers; when a project has a supplement, Jake can say: "Load the math skill and read this project's CLAUDE_MATH.md before we begin," or the project's own CLAUDE.md can point to the supplement. The project supplement overrides the general skill only where it explicitly says so; otherwise both apply.

### 16.5 Keep it current

When a mathematical failure mode appears during the project --- a theorem mismatch, a missed uniformity condition, a sign error in a tilted measure, a misidentified estimand --- add it to the supplement. The supplement accrues value over the life of the project. An AI reading it at the start of the next session inherits the hard-won lessons of the previous ones.

### 16.6 Template

A minimal starting supplement might look like:

```
# CLAUDE_MATH.md (project: <name>)

## Project scope
<one paragraph>

## Notation
<symbol table or prose>

## Key theorems invoked
<list with references and exact hypotheses>

## Subfield-specific checks
<what to verify every time>

## Simulation conventions
<standard designs>

## Failure modes observed in this project
<running list>

## Key references
<annotated list>
```

---

