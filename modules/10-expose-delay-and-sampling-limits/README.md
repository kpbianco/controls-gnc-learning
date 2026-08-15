# P10 — Expose Delay and Sampling Limits

**Track:** Controls, State Estimation, Guidance, and Navigation  
**Phase 3:** Digital and constrained control  
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you expose Delay and Sampling Limits?

## Computational mental model

P09 made the digital update and zero-order hold visible. P10 keeps the normalized
continuous plant `y' = -y + u` and uses the deliberately simple sampled feedback law

`uComputed[k] = Kp*(1-y[k])`, with `Kp = 8`.

Sampling and computation are separate events. At each sample, the controller starts
computing a new command. For `Td` seconds the actuator retains the previous command;
for the remaining `Ts-Td` seconds it applies the new one. The plant moves throughout
both pieces. Its exact sample transition is

`y[k+1] = a*y[k] + wOld*u[k-1] + wNew*u[k]`,

where `a = exp(-Ts)`, `wOld = exp(-(Ts-Td))*(1-exp(-Td))`, and
`wNew = 1-exp(-(Ts-Td))`. Increasing `Ts` lengthens the hold. Increasing `Td` moves
weight from the current correction to the stale one.

The continuous proportional target settles to `8/9 output` rather than the unit
reference because proportional control retains steady-state error. That known P05
effect is held fixed here so timing is the only mechanism under study.

Time, sample period, and computation delay use seconds. Sample rate and bandwidth use
hertz (`Hz`); closed-loop bandwidth also appears in radians per second (`rad/s`).
Output, reference, and control effort use normalized `output` units. Delay fraction,
Nyquist ratio, pole magnitude, and proportional gain are dimensionless; delay phase
uses degrees.

## Learning flow

1. Predict whether computation delay first appears in the command or plant output.
2. Compare the deterministic `Ts = 0.05 s`, `Td = 0.01 s` baseline with immediate
   continuous feedback.
3. Sweep `Ts` with zero computation delay and observe target gap and pole movement.
4. Reset `Ts = 0.1 s`, sweep `Td`, and observe stale-command time, phase, and overshoot.
5. Break the prompt-feedback assumption with `Ts = 0.2 s`, `Td = 0.18 s` even though
   the simple Nyquist ratio remains above one.
6. Recover by reducing only `Td` to `0.02 s` while preserving `Ts`, gain, and plant.
7. Run the numerical checks and give a two-sentence teach-back.

## Artifact map and dependencies

- `lesson.m` starts the concept-first notebook path.
- `model.m` owns exact two-piece plant motion, command timing, explicit two-state
  pole arithmetic, validation, metrics, and resource bounds without presentation.
- `experiment.m` owns labeled baseline views, two isolated sweeps, broken case, and
  same-sample-period recovery.
- `interactive.m` exposes bounded sample-period and delay-fraction controls with reset.
- `lesson.md` and `walkthrough.md` connect P05 feedback and prerequisite P09 timing.
- `checks.md` and `run_checks.m` cover independent identities, limiting cases,
  malformed inputs, failure, recovery, and resource caps.

Base MATLAB is the only declared dependency. No controller conversion, transfer-
function, state-space, root-finding, or simulation toolbox shortcut is used. Retained
repository checks are static and use independent reference arithmetic. No MATLAB-
runtime, rendered UI, MATLAB numerical-fidelity, bench, HIL, field, or production
evidence is claimed for P10.
