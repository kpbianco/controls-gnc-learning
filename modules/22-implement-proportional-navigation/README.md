# P22 — Implement Proportional Navigation

**Track:** Controls, State Estimation, Guidance, and Navigation

**Phase 6:** Guidance and HIL

**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you implement Proportional Navigation?

## Physical mental model

P21 produced a feasible reference under declared kinematic limits. P22 adds relative guidance: an
interceptor does not aim at the target's current position; it turns to remove rotation of the line joining
them. With relative position `r = p_target - p_interceptor` and relative velocity `v_rel`, the transparent
planar measurements are

```text
range      R         = sqrt(r_x^2 + r_y^2)
closing    Vc        = -dot(r,v_rel)/R
LOS rate   lambdaDot = (r_x*v_rel_y - r_y*v_rel_x)/R^2
command    a_cmd     = N*max(Vc,0)*lambdaDot
```

The command is lateral acceleration in `m/s^2`; `N` is dimensionless. Positive closing speed means range
is shrinking. An intercept is indicated by decreasing range and line-of-sight rate moving toward zero:
constant bearing, decreasing range. The model clips the applied acceleration to `±a_max`, then advances
heading explicitly with `psi_next = psi + (a_applied/speed)*dt`.

This is a deterministic, sampled, idealized 2-D guidance model. It is not an autopilot, actuator-dynamics,
collision-safety, hardware, or continuous-time fidelity claim.

## Baseline and learner controls

The baseline interceptor starts at `[0,0] m`, travels at constant `300 m/s` along `+x`, and pursues a target
starting at `[5000,600] m` with `60 m/s` crossing speed. It uses `N=3`, an `80 m/s^2` acceleration limit,
`0.02 s` step, `25 s` horizon, and `5 m` capture radius.

- Navigation constant `N`, `0–8`: scales the response to the same closing speed and LOS rate.
- Target crossing speed, `-150–150 m/s`: changes the initial relative geometry rate.
- Acceleration limit, `5–120 m/s^2`: clips the turn that the vehicle can actually apply.
- Reset: restores `N=3`, `60 m/s`, and `80 m/s^2`.

The first independent sweep varies only `N = [1 2 3 4 5]`. The second resets `N` and varies only
acceleration authority `[5 10 20 40 80] m/s^2`. The deliberately broken `5 m/s^2` case sustains
clipping, reaches a closest approach hundreds of metres away, and exits at the time limit. A fresh
baseline call exactly recovers because the model owns no hidden or persistent state.

## Run it

From the repository root, use `launch_lesson("P22")`. To open only the UI while preventing another
module's generic `model` function from winning path resolution:

```matlab
moduleFolder = fullfile(pwd,"modules","22-implement-proportional-navigation");
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

Run checks with `run_module_checks("P22")`.

## Evidence boundary

The retained Python oracle independently reproduces the discrete recurrence and event interpolation.
No MATLAB-runtime, rendered-UI, MATLAB numerical-fidelity, autopilot, bench, HIL, field, RT1/RT2,
Unreal, signing, deployment, staging, release, or production validation is implied without separate
retained evidence.
