# P20 — Compare Nominal and Robust Designs

**Track:** Controls, State Estimation, Guidance, and Navigation

**Phase 5:** Optimal and robust control

**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you compare Nominal and Robust Designs?

## Physical mental model

P19 measured how actuator effectiveness `b` and drag `a` separate predicted and actual speed. P20
uses the same exact held-input plant and asks a design question: should a controller be judged only
at `a=b=1`, or across a declared set of plausible plants?

```text
v[k+1] = exp(-a*dt)*v[k] + (b/a)*(1-exp(-a*dt))*u[k]

nominal: u_N[k] = (a0/b0)*r[k] + K_N*(r[k]-v_N[k])
robust:  u_R[k] = Kp*(r[k]-v_R[k]) + Ki*z[k]
         z[k+1] = z[k] + dt*(r[k]-v_R[k])
```

The nominal design inherits P19's model-matched feedforward and proportional correction. It is
faster on the matched plant. The robust design is selected from 12 visible `(Kp,Ki)` candidates by
minimizing worst-case tracking-error integral over 25 positive actuator/drag scenarios, subject to
stability and a `90 m^2/s^3` worst-case command-effort limit. Selection uses a `1 m/s` step,
12-second horizon, and `dt=0.02 s`. This is a narrow finite-grid claim,
not a promise against arbitrary delay, saturation, polarity, noise, or unmodeled dynamics.

## Learner controls

- Actuator gain ratio `0.5–1.5`: command effectiveness relative to the nominal model.
- Drag ratio `0.5–2`: speed loss relative to the nominal model.
- Reference speed `0–2 m/s`: exploratory amplitude; only `1 m/s` is inside the effort-selection claim.
- Actuator polarity: the deliberately broken negative choice lies outside the design grid.
- Reset: restores both ratios to one, `1 m/s`, and positive polarity.

The complementary views show speed in `m/s`, command in `m/s^2`, tracking ISE in `m^2/s`, command
effort in `m^2/s^3`, final error in `m/s`, and discrete pole magnitude. Sweep actuator gain with drag
fixed, reset, then sweep drag with actuator gain fixed.

## Run it

From the repository root, use `launch_lesson("P20")`. To open only the UI while preventing another
module's generic `model` function from winning path resolution:

```matlab
moduleFolder = fullfile(pwd,"modules","20-compare-nominal-and-robust-designs");
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

Run checks with `run_module_checks("P20")`.

## Evidence boundary

The retained Python oracle independently propagates the equations and repeats the finite design
search. No MATLAB-runtime, rendered-UI, numerical-fidelity, bench, HIL, field, RT1/RT2, Unreal,
signing, deployment, or production validation is implied without separate retained evidence.
