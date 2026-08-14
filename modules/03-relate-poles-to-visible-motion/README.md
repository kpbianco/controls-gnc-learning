# P03 — Relate Poles to Visible Motion

**Track:** Controls, State Estimation, Guidance, and Navigation  
**Phase 1:** Dynamic systems  
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you relate Poles to Visible Motion?

## Mental model

A free second-order mode with poles `p = sigma +/- j*omega` obeys

```text
x'' - 2*sigma*x' + (sigma^2 + omega^2)*x = 0.
```

The pole real coordinate `sigma` has units `1/s` and sets whether the motion's
exponential envelope shrinks or grows. The imaginary magnitude `omega` has units
`rad/s` and sets the oscillation period `2*pi/omega`. Initial displacement and
velocity decide the phase and amplitude that are visible inside that envelope.

## What to run

1. Open `lesson.m` for the question, P02 bridge, and one baseline prediction.
2. Run `experiment.m` one `%%` section at a time: baseline motion, pole-plane
   view, real-part sweep, imaginary-part sweep, then broken and recovered cases.
3. Run `interactive.m`; move one coordinate, reset, then move the other.
4. Run `run_checks.m`, answer `checks.md`, and give the teach-back.

The implementation uses transparent exact equations and base MATLAB operations. It
does not require Control System Toolbox transfer functions or hidden solvers.

## Evidence boundary

The model is deterministic simulation content. Repository tests statically validate
the artifact and reference-arithmetic contracts. MATLAB runtime, rendered figures,
UI callbacks, MATLAB numerical fidelity, educational efficacy, bench, hardware,
HIL, field, and production behavior require separate retained evidence.
