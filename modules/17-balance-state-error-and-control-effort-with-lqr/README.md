# P17 — Balance State Error and Control Effort with LQR

**Track:** Controls, State Estimation, Guidance, and Navigation  
**Phase 5:** Optimal and robust control  
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you balance State Error and Control Effort with LQR?

## Physical mental model

P16 estimated the position and rate of a damped cart. P17 treats that two-state estimate as the error
to regulate. A quadratic score charges for normalized position error, normalized rate error, and
normalized commanded acceleration:

```text
x = [position error; rate error]
J = dt * sum(q_p*(p/1 m)^2 + (v/(1 m/s))^2 + r*(u/(1 m/s^2))^2)
u = -K*x
K = (R + B'*P*B)^(-1) * B'*P*A
```

`Q=diag(q_p,1)` says which state errors are expensive, while scalar `R=r` says how expensive control
effort is. The model exposes the Riccati iteration that turns future cost `P` into `K`; it does not
call an LQR, Riccati, state-space, or simulation toolbox helper. The one-unit normalization scales
keep the summed terms dimensionless while plots and physical metrics retain metres, seconds, and
acceleration units. Multiplying every stage and terminal term by the same positive `dt` gives the
integrated score units of seconds without changing the minimizing gain.

## Learning flow

1. Read the cost, feedback, and Riccati equations and make one prediction.
2. Visualize the deterministic baseline state response and commanded/applied acceleration.
3. Move only position-error weight `q_p`; observe higher position gain, less accumulated position
   error, and a larger squared-command effort integral.
4. Reset `q_p`, move only control-effort weight `r`; observe gentler commands, a lower effort integral,
   and slower settling.
5. Explain the tradeoff from `Q`, `R`, and future cost rather than from MATLAB syntax.
6. Disconnect the actual actuator while retaining the nominal design and recognize persistent error,
   nonzero requested effort, and zero applied effort.
7. Restore full authority, run deterministic checks, and give a two-sentence teach-back.

## Run

From MATLAB with the repository as the current folder:

```matlab
launch_lesson("P17")
moduleFolder = fullfile(pwd,"modules","17-balance-state-error-and-control-effort-with-lqr");
addpath(moduleFolder,"-begin");
clear model interactive;
try
    interactive
catch exception
    rmpath(moduleFolder);
    rethrow(exception)
end
rmpath(moduleFolder);
clear moduleFolder
run_module_checks("P17")
```

The module path is temporary so its generic `model`, `interactive`, and `run_checks` names cannot
shadow a neighboring lesson in a long-lived MATLAB session. All calculations are deterministic base
MATLAB arithmetic. Retained evidence is static plus independent Python reference simulation. No MATLAB-runtime,
UI, MATLAB numerical-fidelity, bench, HIL, field, or production validation is implied.
