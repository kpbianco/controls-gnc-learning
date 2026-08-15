# P11 — Drive an Actuator into Saturation

**Track:** Controls, State Estimation, Guidance, and Navigation  
**Phase 3:** Digital and constrained control  
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you drive an Actuator into Saturation?

## Physical mental model

P05 exposed proportional feedback and P10 separated the command a controller computes
from the command an actuator receives. P11 fixes the timing and adds an amplitude limit
to the same normalized first-order plant,

`tau*y' = -y + g*uApplied`, with `uRequested = Kp*(r-y)`.

Here `tau=1 s`, plant gain `g=1 output/actuator`, and controller gain
`Kp=4 actuator/output`.

The actuator applies the symmetric clamp

`uApplied = min(max(uRequested,-uLimit),uLimit)`.

The missing command `uRequested-uApplied` is not hidden. While it is nonzero, the
actuator is saturated and the plant moves under the bounded applied input. For one
held interval `dt`, the exact plant transition is

`yNext = exp(-dt/tau)*y + (1-exp(-dt/tau))*g*uApplied`.

The unlimited proportional equilibrium is `yEq = g*Kp*r/(1+g*Kp)`, or `4*r/5`
with the declared gains. If `uLimit` is no greater than the required equilibrium
command magnitude `abs(yEq/g)`, clipping persists. If `abs(r)>g*uLimit`, the plant
cannot reach the requested output even under continuously maximum actuation.
This lesson uses no integral state: accumulated integral error and anti-windup belong
to prerequisite-dependent P12.

Time uses seconds (`s`). Output and reference use normalized `output` units. Requested
control, applied control, clipping gap, and actuator limit use normalized `actuator`
units. `Kp` uses `actuator/output`, plant gain uses `output/actuator`, and authority
ratio and saturation fraction are dimensionless.

## Learning flow

1. Predict which trace changes first when a requested command exceeds actuator authority.
2. Compare the deterministic `r=1 output`, `uLimit=2 actuator` baseline with the
   same proportional loop connected to an unlimited actuator.
3. Keep `uLimit=2`, sweep reference amplitude, and observe command deficit and clipped time.
4. Reset `r=1`, sweep actuator limit, and observe release time and tracking error.
5. Break feasibility with `r=1.5`, `uLimit=0.6`, which remains saturated for the full view.
6. Recover by increasing only `uLimit` to `2`, preserving reference, controller, plant,
   time step, and horizon.
7. Run the checks and give a two-sentence teach-back.

## Artifact map and dependencies

- `lesson.m` starts the concept-first notebook path.
- `model.m` owns deterministic clipping, exact held-input propagation, validation,
  metrics, partial intervals, and resource bounds without presentation.
- `experiment.m` owns labeled baseline views, two isolated sweeps, the infeasible
  broken case, and one-limit recovery.
- `interactive.m` exposes bounded reference and actuator-limit controls with reset.
- `lesson.md` and `walkthrough.md` connect P05 feedback and prerequisite P10's
  requested-versus-applied command distinction.
- `checks.md` and `run_checks.m` cover independent identities, limiting cases,
  malformed inputs, failure, recovery, and resource caps.

Base MATLAB is the only declared dependency. No transfer-function, state-space,
root-finding, ODE solver, or simulation toolbox shortcut is used. Retained repository
checks are static and use independent reference arithmetic. No MATLAB-runtime,
rendered UI, MATLAB numerical-fidelity, bench, HIL, field, or production evidence is
claimed for P11.
