# P06 — Tune a PID by Observing Each Term

**Track:** Controls, State Estimation, Guidance, and Navigation  
**Phase 2:** Feedback fundamentals  
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you tune a PID by Observing Each Term?

## Physical mental model

A PID controller pushes a damped 1 kg carriage toward a `1 m` reference while a
constant `-1 N` load pulls back. The controller force is shown as three visible
parts:

- `P = Kp*e` reacts to the error that exists now;
- `I = Ki*integral(e dt)` remembers error and supplies the steady holding force;
- `D = -Kd*v` opposes measured velocity and adds damping without differentiating a
  reference step.

The transparent plant is `m*x'' = P + I + D + Fload - b*x'`. No Control System
Toolbox or opaque solver is used: `model.m` advances these states with explicit,
fixed-step fourth-order Runge-Kutta calculations.
The requested calculation interval controls numerical resolution and plotted
samples; it is not a sampled PID implementation, which belongs to P09.

## Learning flow

1. Establish a deterministic baseline.
2. Show at least two complementary plots or views.
3. Expose meaningful parameters as MATLAB controls or clearly editable Live Editor variables.
4. Sweep two parameters independently.
5. Include one deliberately broken or misleading case.
6. Ask one observation question at a time.
7. Finish with a teach-back and a deterministic check.

## Artifact map

The completed module owns these files:

- `lesson.m` — notebook-style MATLAB sections (`%%`) and concise narrative.
- `interactive.m` — `uifigure` controls, plots, and immediate feedback.
- `model.m` — deterministic calculations separated from presentation.
- `experiment.m` — reproducible baseline, sweeps, and broken case.
- `lesson.md` — tutor-facing explanation and misconceptions.
- `walkthrough.md` — expected observations in order.
- `checks.md` and `run_checks.m` — conceptual and numerical completion checks.

Start with `lesson.m`, run `experiment.m` one section at a time, and then use
`interactive.m` to move `Ki` and `Kd` independently. The broken case reverses the
derivative sign so velocity is reinforced instead of opposed; recovery restores
derivative damping before any retuning.
