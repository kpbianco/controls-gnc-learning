# P08 — Reject a Disturbance with Feedback

**Track:** Controls, State Estimation, Guidance, and Navigation  
**Phase 2:** Feedback fundamentals  
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you reject a Disturbance with Feedback?

## Physical mental model

A normalized first-order plant has one-second time constant and unit static gain:

`tau*y' = -y + u + d`, with `tau = 1 s`.

The reference is zero and proportional feedback uses the measured output,
`u = -K*y_m`. When the sensor is honest, `y_m = y`, so a constant plant-input
disturbance has `y_ss = d/(1+K)`. Feedback reduces the disturbance by the
sensitivity factor `1/(1+K)`, but it spends control effort and does not erase the
offset with proportional action alone. P06's integral term is the mechanism that
could remove a constant residual; P07 warns that added loop action must retain
stability margin.

For a sinusoidal disturbance at angular frequency `omega`, the exact disturbance
path is

`|Y/D| = 1/sqrt((1+K)^2 + (tau*omega)^2)`.

The uncontrolled plant already filters fast disturbances. The additional benefit
of feedback is therefore strongest at low frequency and approaches one at high
frequency. The broken case changes disturbance location: a sensor bias enters the
measurement, not the plant. High gain then drives the true output away from zero
to make the biased measurement look small.

Output, plant-input disturbance, sensor bias, and control effort use normalized
`output` units; gain and rejection ratios are dimensionless; time is seconds;
angular frequency is radians per second.

## Learning flow

1. Read the mechanism and predict how a larger feedback gain changes a constant
   load's output deviation.
2. Visualize the deterministic step-disturbance baseline in time and frequency.
3. Sweep feedback gain while disturbance amplitude, location, and frequency stay fixed.
4. Reset gain and sweep disturbance frequency independently.
5. Break the honest-sensor assumption with a constant measurement bias.
6. Recover by removing the bias after validating the sensor, rather than by
   increasing gain.
7. Run the numerical checks and give a two-sentence teach-back.

## Artifact map and dependencies

- `lesson.m` starts the concept-first learner path.
- `model.m` owns deterministic RK4 and exact sensitivity calculations.
- `experiment.m` owns baseline, both independent sweeps, broken case, and recovery.
- `interactive.m` exposes bounded gain and disturbance-frequency controls.
- `lesson.md` and `walkthrough.md` guide one observation at a time.
- `checks.md` and `run_checks.m` cover interpretation, limits, failure, and recovery.

Base MATLAB is the only declared dependency. The calculation interval controls
numerical resolution; it is not a sampled controller. This repository retains
static checks and independent reference arithmetic, but no MATLAB-runtime, UI,
MATLAB numerical-fidelity, bench, HIL, field, or production evidence for P08.
