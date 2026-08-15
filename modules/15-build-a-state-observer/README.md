# P15 — Build a State Observer

**Track:** Controls, State Estimation, Guidance, and Navigation  
**Phase 4:** State-space control  
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you build a State Observer?

## Physical mental model

P14 established that a history of cart-position measurements reveals both position and rate. P15
uses that visibility in real time. A model predicts the next state from the known acceleration
command; the position sensor checks the prediction; and the innovation, `y - C*xhat`, corrects both
estimated position and estimated rate:

```text
x[k+1]    = Ad*x[k]    + Bd*u[k]
xhat[k+1] = Ad*xhat[k] + Bd*u[k] + L*(y[k] - C*xhat[k])
```

The exact sampled plant is the P14 cart:

```text
d(position)/dt = rate
d(rate)/dt     = -0.5*rate + acceleration command
measurement    = position
```

The observer uses the same exact zero-order-hold `Ad` and `Bd`. Its repeated error pole is requested
as `q = exp(-observerPoleSpeed*dt)`, and the two entries of `L` are derived explicitly from the trace
and determinant of `Ad - L*C`. No pole-placement, state-space, simulation, or eigenvalue toolbox
helper hides that operation.

## Learning flow

1. Read the plant, prediction, measurement, innovation, and correction equations.
2. Visualize a deterministic noise-free baseline from a deliberately wrong initial estimate.
3. Move only observer pole speed and compare final error with required correction gain.
4. Reset speed, move only deterministic measurement-interference amplitude, and observe estimate ripple.
5. Explain both effects from the visible error recurrence.
6. Add a `+0.15 m` sensor bias and see innovation become quiet while position remains wrong.
7. Restore calibration, run deterministic checks, and give a two-sentence teach-back.

## Run

From MATLAB with the repository as the current folder:

```matlab
launch_lesson("P15")
moduleFolder = fullfile(pwd,"modules","15-build-a-state-observer");
addpath(moduleFolder,"-begin");
try
    interactive
catch exception
    rmpath(moduleFolder);
    rethrow(exception)
end
rmpath(moduleFolder);
clear moduleFolder
run_module_checks("P15")
```

`launch_lesson` removes its temporary module path when the lesson returns. Add the folder only while
opening the interactive view, as shown. Both the normal and error paths remove it so the generic
module-local function names do not shadow a different module later in the MATLAB session.

The module uses deterministic base MATLAB arithmetic. The sinusoidal measurement interference is a
repeatable teaching input, not stochastic sensor evidence; Kalman filtering belongs to P16. Retained
repository evidence is static plus independent Python reference simulation. No MATLAB-runtime, UI,
MATLAB numerical-fidelity, bench, HIL, field, or production validation is implied.
