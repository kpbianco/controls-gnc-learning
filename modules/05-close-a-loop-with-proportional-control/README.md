# P05 — Close a Loop with Proportional Control

**Track:** Controls, State Estimation, Guidance, and Navigation
**Phase 2:** Feedback fundamentals
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you close a Loop with Proportional Control?

## Mental model

A first-order plant turns command `u` into measured output `y`:

```text
tau*y' = -y + G*u
u = Kp*(r - y).
```

The proportional controller reacts to the present tracking error `e = r - y`.
Closing the loop moves the pole from `-1/tau` to `-(1 + G*Kp)/tau`, so larger
`Kp` makes the response faster. The same equations also reveal the tradeoff:
finite proportional gain needs a nonzero steady error to hold a nonzero command.

## What to run

1. Open `lesson.m` for the P04 bridge and one baseline prediction.
2. Run `experiment.m` one `%%` section at a time: baseline output, error and
   effort, proportional-gain sweep, plant-time-constant sweep, then reversed-sign
   broken and recovered cases.
3. Run `interactive.m`; move proportional gain once, reset, then move plant time
   constant once.
4. Run `run_checks.m`, answer `checks.md`, and give the teach-back.

The model uses an explicit closed-loop equation and exact propagation over each
requested interval. It uses base MATLAB and no Control System Toolbox, Simulink,
transfer-function object, or opaque solver.

## Evidence boundary

The model is deterministic simulation content. Repository tests statically validate
artifacts, equations, independent reference arithmetic, malformed-input contracts,
and resource bounds. MATLAB runtime, rendered figures, UI callbacks, MATLAB
numerical fidelity, educational efficacy, bench, hardware, HIL, field, and
production behavior require separate retained evidence.
