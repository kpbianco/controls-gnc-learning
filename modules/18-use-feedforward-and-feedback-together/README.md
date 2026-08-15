# P18 — Use Feedforward and Feedback Together

**Track:** Controls, State Estimation, Guidance, and Navigation

**Phase 5:** Optimal and robust control

**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you use Feedforward and Feedback Together?

## Physical mental model

A planned plant input knows what nominal motion is coming, so feedforward can act before an error
appears. Feedback cannot anticipate that plan; it watches the measured or estimated tracking error
and corrects what the plan did not predict. The damped cart and state feedback compound directly on
P17, while a fixed load pulse makes the two jobs separately visible.

For `e=x_ref-x`, the held-input model exposes every operation:

```text
x_ref[k+1] = A*x_ref[k] + B*u_plan[k]
u_ff[k]    = s_ff*alpha*u_plan[k]
u_fb[k]    = beta*[Kp Kv]*e[k]
u_cmd[k]   = u_ff[k] + u_fb[k]
x[k+1]     = A*x[k] + B*(u_cmd[k] + d[k])
e[k+1]     = (A-beta*B*K)*e[k] + B*((1-s_ff*alpha)*u_plan[k]-d[k])
```

`u_plan`, `u_ff`, `u_fb`, `u_cmd`, and `d` are plant-input accelerations in `m/s^2`.
`Kp` has `1/s^2`; `Kv` has `1/s`; mixer scales and sign are dimensionless. The plan is a feasible
input trajectory, not a claim that the reference position is sinusoidal.

## Learner controls

- Feedforward scale `alpha`, `0–1.5`: zero makes feedback recreate the known plan; one matches it.
- Feedback scale `beta`, `0–2`: zero cannot remove the position offset left by the load pulse.
- Disturbance magnitude, `0–0.8 m/s^2`: changes only the unplanned one-second load.
- Feedforward polarity: the deliberately broken choice reverses a command-path convention.
- Reset restores `alpha=1`, `beta=1`, `0.4 m/s^2` disturbance, and correct polarity.

The experiment first sweeps feedforward without a disturbance, resets, then sweeps feedback with the
same disturbance. It finally reverses feedforward polarity and restores the exact baseline.

## Run it

From the repository root, use `launch_lesson("P18")`. To open only the UI while preventing another
module's generic `model` function from winning path resolution:

```matlab
moduleFolder = fullfile(pwd,"modules","18-use-feedforward-and-feedback-together");
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

Run checks with `run_module_checks("P18")`.

## Evidence boundary

The retained Python oracle independently simulates the declared recurrence. No MATLAB-runtime,
rendered-UI, numerical-fidelity, bench, HIL, field, RT1/RT2, Unreal, signing, deployment, or
production validation is implied without separately retained evidence.
