# P07 — See Stability Margin in Time and Frequency

**Track:** Controls, State Estimation, Guidance, and Navigation  
**Phase 2:** Feedback fundamentals  
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you see Stability Margin in Time and Frequency?

## Physical mental model

P06 tuned a controller by watching its terms. P07 asks how much unseen dynamics
that tuning can tolerate. A unity-feedback loop uses gain `K` (`1/s^2`) to
command a plant `1/[s(s+b)]`, whose damping rate is `b = 1/s`, through a
first-order actuator with lag `tau`:

`L(s) = K / (s(s+b)(tau*s+1))`.

The time view advances the matching plant and actuator states with explicit
fixed-step fourth-order Runge-Kutta calculations. The frequency view evaluates
the same factors directly at `s = j*omega`; it does not call a transfer-function,
margin, root, or simulation toolbox. Gain crossover is where the open loop
returns with unity magnitude. Phase margin says how much additional phase lag fits
there before negative feedback behaves like positive feedback.

Normalized plant output has unit `output`; velocity has `output/s`; actuator and
controller command have `output/s^2`; and actuator rate has `output/s^3`. The
loop response and gain-margin ratio are dimensionless. For `b = 1/s` and `tau >
0`, phase crossover is `omega_pc = sqrt(b/tau)` and critical gain is
`Kcritical = b*(1+b*tau)/tau` in `1/s^2`. Thus gain margin is
`Kcritical/K`. These independent identities connect the displayed frequency
margins to the time response.

## Learning flow

1. Read the mechanism and make one prediction about the effect of actuator lag.
2. Visualize the deterministic baseline first in time, then in frequency.
3. Sweep loop gain while actuator lag remains fixed.
4. Reset gain and sweep actuator lag independently.
5. Break the zero-lag assumption: a gain that looks bounded with an instantaneous
   actuator becomes unstable when `tau = 0.5 s`.
6. Recover by reducing gain below the lag-dependent critical value.
7. Run the numerical checks and give a two-sentence teach-back.

## Artifact map and dependencies

- `lesson.m` starts the concept-first learner path.
- `model.m` owns deterministic time and frequency calculations.
- `experiment.m` owns baseline, both sweeps, broken case, and recovery views.
- `interactive.m` exposes bounded loop-gain and actuator-lag controls.
- `lesson.md` and `walkthrough.md` guide one observation at a time.
- `checks.md` and `run_checks.m` cover interpretation and numerical invariants.

Base MATLAB is the only declared dependency. The calculation interval controls
numerical resolution; it is not a sampled controller. This repository retains
static checks, but no MATLAB-runtime, UI, numerical-fidelity, bench, HIL, field,
or production evidence for P07.
