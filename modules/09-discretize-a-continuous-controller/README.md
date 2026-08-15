# P09 — Discretize a Continuous Controller

**Track:** Controls, State Estimation, Guidance, and Navigation  
**Phase 3:** Digital and constrained control  
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you discretize a Continuous Controller?

## Computational mental model

P08 used a continuous feedback law around the normalized first-order plant

`y' = -y + u`.

P09 gives that plant a digital PI controller. The intended continuous controller is

`u = Kp*e + Ki*integral(e dt)`, with `e = r-y`, `Kp = 2`, and `Ki = 4 1/s`.

A digital controller sees error only at sample instants and holds its command between
them. The plant still evolves continuously during each hold:

`y[k+1] = exp(-Ts)*y[k] + (1-exp(-Ts))*u[k]`.

Forward Euler integrates the previous sample's error; backward Euler integrates the
current sample's error. Both approach the continuous PI target as sample period `Ts`
shrinks, but they place the discrete closed-loop poles differently at finite `Ts`.
The visible consequences are staircase control effort, tracking gap, overshoot, and—
at pole magnitude one—loss of asymptotic convergence. Magnitudes above one produce
growth.

Output, reference, error, and control effort use normalized `output` units. Time and
sample period use seconds. `Kp`, pole magnitude, and samples per natural period are
dimensionless; `Ki` uses `1/s`.

## Learning flow

1. Predict how a held digital command differs from the continuous PI command.
2. Compare a deterministic `Ts = 0.05 s` backward-Euler baseline with the continuous target.
3. Sweep sample period while the rule and gains remain fixed.
4. Reset `Ts`, then compare forward and backward Euler independently.
5. Break the resolved-sampling assumption with `Ts = 0.8 s` and forward Euler.
6. Recover by reducing `Ts`, not by trusting a smooth line drawn through sparse samples.
7. Run the numerical checks and give a two-sentence teach-back.

## Artifact map and dependencies

- `lesson.m` begins the concept-first learner path.
- `model.m` owns the transparent controller updates, exact held-plant transition,
  continuous target, pole arithmetic, metrics, validation, and resource bounds.
- `experiment.m` owns the baseline, two independent sweeps, broken case, and recovery.
- `interactive.m` exposes bounded sample-period and discretization-rule controls.
- `lesson.md` and `walkthrough.md` guide one observation at a time.
- `checks.md` and `run_checks.m` cover invariants, limits, malformed inputs,
  discretization failure, and recovery.

Base MATLAB is the only declared dependency; no `c2d`, transfer-function, state-space,
or simulation toolbox shortcut is used. Retained repository checks are static and use
independent reference arithmetic. No MATLAB-runtime, UI, MATLAB numerical-fidelity,
bench, HIL, field, or production evidence is claimed for P09.
