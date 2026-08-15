# P19 — Measure Sensitivity to Model Error

**Track:** Controls, State Estimation, Guidance, and Navigation

**Phase 5:** Optimal and robust control

**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you measure Sensitivity to Model Error?

## Physical mental model

P18 used feedforward for a known nominal input and feedback for observed tracking error. P19 now asks
what happens when the model behind that nominal expectation is slightly wrong. A speed servo predicts
motion with nominal drag `a0` and actuator effectiveness `b0`, while an independently propagated
actual plant uses `a` and `b`:

```text
u[k]     = (a0/b0)*r[k] + K*(r[k]-v[k])
v[k+1]   = exp(-a*dt)*v[k] + (b/a)*(1-exp(-a*dt))*u[k]
```

The controller samples speed every `dt=0.02 s` and holds `u[k]` over that interval. The update is the
exact held-input solution of `dv/dt=-a*v+b*u`; its pole therefore belongs to the sampled-data loop,
not to an assumed continuously updated controller.

The prediction gap is `v_actual-v_predicted` in `m/s`. A local sensitivity is the change in steady
speed divided by a unit fractional parameter change, so its sign says which way the output moves and
its magnitude says how strongly. At the nominal `1 m/s` baseline, actuator-gain sensitivity is
`+0.4 m/s per fraction` and drag sensitivity is `-0.4 m/s per fraction`.

## Learner controls

- Actuator gain ratio `0.5–1.5`: changes command effectiveness while drag stays fixed.
- Drag ratio `0.5–2`: changes speed loss while actuator effectiveness stays fixed.
- Reference speed `0–2 m/s`: scales the experiment without changing its mechanism.
- Actuator polarity: the deliberately broken choice reverses the feedback convention.
- Reset restores both ratios to one, `1 m/s`, and correct polarity.

The experiment sweeps actuator gain, resets, sweeps drag, then reverses actuator polarity. The first
two are bounded parameter errors. The last is a failed structural assumption: the closed-loop pole
moves outside the unit circle, feedback reinforces error, and steady-response sensitivity is undefined.

## Run it

From the repository root, use `launch_lesson("P19")`. To open only the UI while preventing another
module's generic `model` function from winning path resolution:

```matlab
moduleFolder = fullfile(pwd,"modules","19-measure-sensitivity-to-model-error");
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

Run checks with `run_module_checks("P19")`.

## Evidence boundary

The retained Python oracle independently propagates the declared recurrence and checks the analytic
equilibrium sensitivities. No MATLAB-runtime, rendered-UI, numerical-fidelity, bench, HIL, field,
RT1/RT2, Unreal, signing, deployment, or production validation is implied without separate evidence.
