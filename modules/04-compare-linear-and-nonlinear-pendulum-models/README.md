# P04 — Compare Linear and Nonlinear Pendulum Models

**Track:** Controls, State Estimation, Guidance, and Navigation
**Phase 1:** Dynamic systems
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you compare Linear and Nonlinear Pendulum Models?

## Mental model

A pendulum with angle `theta`, length `L`, gravitational acceleration `g`, and
linearized damping ratio `zeta` obeys

```text
nonlinear: theta'' + 2*zeta*sqrt(g/L)*theta' + (g/L)*sin(theta) = 0
linear:    theta'' + 2*zeta*sqrt(g/L)*theta' + (g/L)*theta = 0.
```

The linear model replaces `sin(theta)` with `theta`. That approximation is strong
near zero because the two restoring terms nearly coincide. At large release angles,
`sin(theta)` has smaller magnitude than `theta`, so the real pendulum restores more
slowly and its motion falls behind the linear prediction.

## What to run

1. Open `lesson.m` for the P03 bridge and one baseline prediction.
2. Run `experiment.m` one `%%` section at a time: baseline motion, restoring-law
   view, release-angle sweep, length sweep, then broken and recovered cases.
3. Run `interactive.m`; move release angle once, reset, then move length once.
4. Run `run_checks.m`, answer `checks.md`, and give the teach-back.

The implementation uses visible fixed-step Runge-Kutta arithmetic and base MATLAB.
It does not use an ODE solver, Simulink, or Control System Toolbox.

## Evidence boundary

The model is deterministic simulation content. Repository tests statically validate
artifacts, equations, reference arithmetic, malformed-input contracts, and resource
bounds. MATLAB runtime, rendered figures, UI callbacks, MATLAB numerical fidelity,
educational efficacy, bench, hardware, HIL, field, and production behavior require
separate retained evidence.
