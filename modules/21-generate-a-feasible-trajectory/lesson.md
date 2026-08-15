# P21 lesson: Generate a Feasible Trajectory

## Guiding question

What inputs, observable effects, and failure modes matter when you generate a Feasible Trajectory?

## Compounds on P20

P20 compared controllers only over a declared uncertainty set and command-effort limit. P21 brings that
boundary-first reasoning into guidance: before asking a controller to follow a reference, test whether the
reference's own kinematic demands fit declared speed and acceleration limits.

## Mental model

Imagine moving a vehicle along one straight axis from rest at zero metres to rest at `xf` metres. A quintic
time law gives position, speed, and acceleration that join smoothly at both ends:

```text
tau = t/T
h(tau)   = 10*tau^3 - 15*tau^4 + 6*tau^5
h'(tau)  = 30*tau^2 - 60*tau^3 + 30*tau^4
h''(tau) = 60*tau - 180*tau^2 + 120*tau^3
```

Position is `xf*h`, speed is `(xf/T)*h'`, and acceleration is `(xf/T^2)*h''`. The shape in normalized time
does not change when duration changes; only its physical time scale and derivative demands change.

## What the exact peaks reveal

- Peak speed occurs halfway through the move and equals `(15/8)*abs(xf)/T`.
- Peak acceleration magnitude occurs at normalized times `(3-sqrt(3))/6` and `(3+sqrt(3))/6`, and equals
  `(10*sqrt(3)/3)*abs(xf)/T^2`.
- Peak jerk magnitude occurs at the endpoints and equals `60*abs(xf)/T^3`.
- The speed constraint requires `T >= (15/8)*abs(xf)/vmax`.
- The acceleration constraint requires `T >= sqrt((10*sqrt(3)/3)*abs(xf)/amax)`.
- The larger duration bound is the active constraint. A zero-distance move has zero demand and no active
  constraint.

These analytic peaks determine feasibility. A plotted sample grid is only a visualization and can miss the
exact acceleration peak between samples.

## Deliberately broken request

Request `20 m` in `4 s` while retaining `5 m/s` and `2 m/s^2` limits. The polynomial remains smooth and
hits both endpoints, but its peak speed is `9.375 m/s` and peak acceleration is about `7.217 m/s^2`.
Smooth is not the same as feasible. A fresh `8 s` call exactly recovers the baseline because the model has
no persistent state or partial plan to roll back.

## Misconceptions to correct directly

- A smooth path is not automatically feasible.
- More plot samples do not reduce the physical speed or acceleration demand.
- Tightening a limit changes the feasibility verdict, not the already chosen polynomial trajectory.
- Doubling duration halves peak speed, quarters peak acceleration, and divides peak jerk by eight.
- Reversing the target changes derivative signs but not absolute utilization.
- Feasible reference generation does not prove closed-loop tracking, collision avoidance, actuator
  feasibility, HIL behavior, or field safety.
- Independent reference arithmetic is not MATLAB-runtime or rendered-UI evidence.

Ask one observation question at a time. Request the teach-back only after executable checks pass.
