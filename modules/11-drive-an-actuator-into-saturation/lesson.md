# P11 lesson: Drive an Actuator into Saturation

## Guiding question

What inputs, observable effects, and failure modes matter when you drive an Actuator into Saturation?

## Compounds on

P05 established proportional feedback. P10, the direct prerequisite, separated a
newly computed command from the command actually applied to the plant. P11 holds
timing fixed and asks what changes when actuator amplitude—not timing—is constrained.

## Tutor path

Ask one prediction: when `uRequested` exceeds `uLimit`, which trace shows the limit
first? Then reveal the baseline output view before the command view.

The controller requests, with `Kp=4 actuator/output`,

`uRequested = 4*(r-y)`.

The actuator applies

`uApplied = min(max(uRequested,-uLimit),uLimit)`.

For `tau=1 s` and plant gain `g=1 output/actuator`, each held interval moves as

`yNext = exp(-dt/tau)*y + (1-exp(-dt/tau))*g*uApplied`.

That equation explains the observation: the output stays continuous, but it rises
more slowly because the missing command never reached the plant. The gap
`uRequested-uApplied` is the most direct saturation symptom.

Move reference amplitude while holding actuator limit fixed. After the learner names
the longer clipped interval, reset reference and move only the limit. Connect shorter
clipping and lower tracking error to increased physical authority, not a change in
controller gain.

For the broken case, `r=1.5 output` and `uLimit=0.6 actuator`. Constant maximum
actuation can approach only `y=0.6 output`, so the target is infeasible and clipping
persists. Recover by changing only `uLimit` to `2 actuator`.

## Misconceptions to correct directly

- Saturation is not merely a flat-looking plot; it is a mismatch between requested
  and applied physical effort.
- A faster sample rate cannot create missing actuator authority.
- Proportional error during saturation is not integrator windup. P11 has no integral
  state; P12 will show what changes when an integrator accumulates this error.
- A target can be physically infeasible even though the code continues to produce
  finite numbers.
- The reference, controller gain, and actuator limit are different quantities with
  different units and roles.

## Completion

Run `run_checks.m`, ask the interpretation questions in `checks.md` one at a time,
and request the two-sentence teach-back. Static repository checks do not establish
MATLAB runtime, UI behavior, numerical fidelity, bench, HIL, field, or production
validation.
