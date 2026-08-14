# P02 — Build Intuition for Integrators and First-Order Systems

**Track:** Controls, State Estimation, Guidance, and Navigation  
**Phase 1:** Dynamic systems  
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you build Intuition for Integrators and First-Order Systems?

## Physical mental model

An integrator is a perfect accumulator: a constant input keeps adding to its state, so its output ramps without a finite steady value. A first-order system also stores history, but its present output leaks toward the commanded equilibrium. Its time constant sets how quickly the remaining gap shrinks.

The two governing equations stay visible throughout the lesson:

```text
dx_I/dt = u
tau * dy/dt + y = K * u
```

Under a constant normalized command `A`, the transparent reference solutions are
`x_I(t) = A*t` and `y(t) = K*A*(1 - exp(-t/tau))`.

## Required learning flow

1. Establish a deterministic baseline.
2. Show at least two complementary plots or views.
3. Expose meaningful parameters as MATLAB controls or clearly editable Live Editor variables.
4. Sweep two parameters independently.
5. Include one deliberately broken or misleading case.
6. Ask one observation question at a time.
7. Finish with a teach-back and a deterministic check.

## Implementation contract

The completed module owns these files:

- `lesson.m` — notebook-style MATLAB sections (`%%`) and concise narrative.
- `interactive.m` — `uifigure` controls, plots, and immediate feedback.
- `model.m` — deterministic calculations separated from presentation.
- `experiment.m` — reproducible baseline, sweeps, and broken case.
- `lesson.md` — tutor-facing explanation and misconceptions.
- `walkthrough.md` — expected observations in order.
- `checks.md` and `run_checks.m` — conceptual and numerical completion checks.

Prefer base MATLAB. Optional toolbox comparisons may be added only after the underlying operation is visible.

## Run the module

From MATLAB, use `launch_lesson("P02")`, or enter this folder and run one section of
`experiment.m` at a time. Open `interactive.m` after observing the baseline. Run
`run_checks.m` before attempting the interpretation questions and teach-back.

## Dependency and evidence boundary

P02 compounds on P01's visible state evolution: the mass response contained both
storage and dissipation, while this module isolates ideal accumulation from one simple
leak-to-equilibrium mechanism. The implementation uses deterministic base-MATLAB
calculations. Repository checks validate structure and equations statically; they do
not claim MATLAB-runtime, UI, numerical-fidelity, bench, HIL, field, or production
validation.
