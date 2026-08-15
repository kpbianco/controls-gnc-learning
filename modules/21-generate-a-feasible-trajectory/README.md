# P21 — Generate a Feasible Trajectory

**Track:** Controls, State Estimation, Guidance, and Navigation

**Phase 6:** Guidance and HIL

**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you generate a Feasible Trajectory?

## Physical mental model

P20 required a controller claim to name its tested plant set and limits. P21 applies the same discipline
before control begins: a reference path is useful only when its demanded speed and acceleration fit the
declared limits. A rest-to-rest quintic move from zero to a target position uses normalized time
`tau=t/T`:

```text
h(tau) = 10*tau^3 - 15*tau^4 + 6*tau^5
x(t)   = xf*h(tau)
v(t)   = (xf/T)*h'(tau)
a(t)   = (xf/T^2)*h''(tau)
```

The endpoints have zero speed and acceleration. Time scaling is the important lever: peak speed scales
as `1/T`, peak acceleration as `1/T^2`, and peak jerk as `1/T^3`. The exact feasibility tests are

```text
peak speed        = (15/8)*abs(xf)/T
peak acceleration = (10*sqrt(3)/3)*abs(xf)/T^2
minimum duration  = max((15/8)*abs(xf)/vmax,
                        sqrt((10*sqrt(3)/3)*abs(xf)/amax))
```

This is a kinematic reference generator, not evidence that a controlled plant can track the reference.

## Learner controls

- Target position `-30–30 m`: changes direction and travel distance.
- Move duration `2–20 s`: changes peak speed, acceleration, and jerk through time scaling.
- Speed limit `0.5–20 m/s`: changes speed utilization and the speed-derived duration bound.
- Acceleration limit `0.1–20 m/s^2`: changes acceleration utilization and its duration bound.
- Reset: restores the feasible `20 m` in `8 s` baseline with `5 m/s` and `2 m/s^2` limits.

The complementary views show position and speed, then acceleration with explicit constraint bands. The
larger exact bound is the minimum feasible duration.
Sweep distance while duration and limits stay fixed; reset, then sweep duration while distance and limits
stay fixed. The deliberately broken `20 m` in `4 s` request stays smooth but exceeds both constraints.

## Run it

From the repository root, use `launch_lesson("P21")`. To open only the UI while preventing another
module's generic `model` function from winning path resolution:

```matlab
moduleFolder = fullfile(pwd,"modules","21-generate-a-feasible-trajectory");
addpath(moduleFolder,"-begin");
clear model interactive;
try
    interactive;
catch exception
    rmpath(moduleFolder);
    rethrow(exception);
end
rmpath(moduleFolder);
```

Run checks with `run_module_checks("P21")`.

## Evidence boundary

The retained Python oracle independently evaluates the quintic equations and analytic peak limits.
No MATLAB-runtime, rendered-UI, numerical-fidelity, plant-tracking, bench, HIL, field, RT1/RT2,
Unreal, signing, deployment, or production validation is implied without separate retained evidence.
