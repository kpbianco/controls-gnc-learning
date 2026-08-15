# P23 — Model Sensor and Actuator Dynamics

**Track:** Controls, State Estimation, Guidance, and Navigation

**Phase 6:** Guidance and HIL

**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you model Sensor and Actuator Dynamics?

## Physical mental model

P22 produced a lateral-acceleration request from line-of-sight geometry, but a request is neither motion nor
a measurement. P23 follows that request through two stored physical states:

```text
actuator:  tau_a * da/dt + a = clip(u, -a_max, +a_max)
sensor:    tau_s * dy/dt + y = a
reported:  y_reported = y + bias
```

Here `u`, `a`, and `y` are requested, applied, and sensed lateral acceleration in `m/s^2`; `tau_a` and
`tau_s` are seconds. The source evaluates the exact zero-order-hold first-order recurrence, including the
finite repeated-pole limit when the time constants are equal. There is no transfer-function, ODE-solver,
Simulink, or identification black box.

The deterministic input alternates between `+20` and `-20 m/s^2`. The baseline holds each sign for `2 s`,
uses actuator `tau_a=0.2 s`, sensor `tau_s=0.1 s`, a `30 m/s^2` actuator limit, zero sensor bias, `0.02 s`
step, and `8 s` duration. The model separates every signal; plots show the request, signed limit lines,
applied motion, reported measurement, and dynamic errors.

## Two levers and failure modes

- Sensor-time-constant sweep `[0 0.02 0.05 0.1 0.2 0.4] s`: only sensor dynamics change; command and
  actuator histories remain exactly identical. A slower sensor reports stale applied motion for longer.
- Actuator-time-constant sweep `[0 0.05 0.1 0.2 0.4 0.8] s`: the request remains identical while a slower
  actuator increases tracking error and may not reach a plateau before reversal.
- Actuator limit: clipping occurs before actuator dynamics. A correct dynamic recurrence cannot create
  unavailable acceleration.
- Sensor bias: bias shifts only the reported value, not the true actuator or sensor dynamic states.
- Broken bandwidth-separation case: a request that reverses every `0.1 s` drives an actuator with
  `tau_a=0.8 s` and sensor with `tau_s=0.6 s`. Applied peak stays below `3 m/s^2`, measured peak below
  `1 m/s^2`, and the stale measurement retains the wrong sign for visible intervals.

Holding the same broken devices and grid while changing only the command half-period to `4 s` restores
peaks above `19 m/s^2` and removes opposite-sign time in the bounded view. A separate fresh baseline call
proves hidden-state isolation.

A fresh baseline call after broken, invalid, or maximum-history calls recovers exactly because the model
has no global, persistent, random, file, network, or asynchronous state.

## Run it

From the repository root, use `launch_lesson("P23")`. To open only the UI while preventing another
module's generic `model` function from winning path resolution:

```matlab
moduleFolder = fullfile(pwd,"modules","23-model-sensor-and-actuator-dynamics");
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

Run checks with `run_module_checks("P23")`.

## Dependencies and evidence boundary

The module uses base MATLAB arithmetic, plotting, and `uifigure` controls only. The retained independent
Python oracle reproduces the exact recurrence and analytic step limits. No MATLAB-runtime, rendered-UI,
MATLAB numerical-fidelity, sensor calibration, actuator characterization, timing, bench, HIL, field,
RT1/RT2, Unreal, signing, deployment, staging, release, or production validation is implied without
separate retained evidence.
