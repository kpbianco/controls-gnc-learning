# P12 — Recover from Integrator Windup

**Track:** Controls, State Estimation, Guidance, and Navigation  
**Phase 3:** Digital and constrained control  
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you recover from Integrator Windup?

## Physical mental model

P11 separated the control effort a feedback law requests from the effort a limited actuator applies.
A PI controller also remembers error in an integral state. If that state keeps growing while the
actuator is pinned, it stores effort the plant never received. When the reference reverses, that old
memory can delay the command reversal and recovery.

P12 compares the same deterministic first-order plant and symmetric actuator limit along two paths:

- unprotected PI: `dI/dt = Ki*e`;
- back-calculation: `dI/dt = Ki*e + Kaw*(uApplied-uRequested)`.

The requested-minus-applied gap is visible rather than hidden in a toolbox block. The correct
back-calculation sign drains unavailable effort; the deliberately broken sign reinforces it.

## Learning flow

1. Read the integral-memory model and make one prediction.
2. Visualize the baseline output, integral state, and applied command.
3. Move only anti-windup gain and inspect recovery error.
4. Reset gain, move only high-demand duration, and inspect stored effort.
5. Explain both changes using the requested-applied command gap from P11.
6. Reverse the back-calculation sign and identify positive feedback from its symptom.
7. Run deterministic checks and give a two-sentence teach-back.

## Run

From MATLAB with the repository as the current folder:

```matlab
launch_lesson("P12")
interactive
run_module_checks("P12")
```

The model uses base MATLAB arithmetic and deterministic inputs. Repository validation retained for
this batch is static plus independent Python reference simulation; no MATLAB-runtime, UI, MATLAB
numerical-fidelity, bench, HIL, field, or production validation is implied.
