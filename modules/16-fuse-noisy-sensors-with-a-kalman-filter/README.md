# P16 — Fuse Noisy Sensors with a Kalman Filter

**Track:** Controls, State Estimation, Guidance, and Navigation  
**Phase 4:** State-space control  
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you fuse Noisy Sensors with a Kalman Filter?

## Physical mental model

P15 predicted the cart state, compared one position measurement with that prediction, and applied a
fixed correction gain. P16 retains the same damped cart but adds a second noisy position sensor and
lets declared uncertainty set the correction at every sample. Prediction carries a state estimate
and covariance forward; the two innovations compare measurements with that prediction; correction
weights each disagreement by how uncertain the prediction and sensors claim to be.

```text
xminus[k] = A*xplus[k-1] + B*u[k-1]
Pminus[k] = A*Pplus[k-1]*A' + Q
innovation = y[k] - C*xminus[k]
S = C*Pminus*C' + R
K = Pminus*C' * S^(-1)
xplus[k] = xminus[k] + K*innovation
```

`Q` has state-covariance units and comes from uncertain acceleration. `R` contains the two position
noise variances in square metres. The model computes the two-by-two covariance inverse explicitly
and uses the Joseph covariance update, so no Kalman, state-space, simulation, or matrix-inverse
toolbox helper hides the governing operation.

## Learning flow

1. Read the predict, innovation, gain, correction, and covariance equations.
2. Visualize a seeded baseline with two raw position sensors, fused position, and reconstructed rate.
3. Move only sensor A's reported noise and see trust shift between sensor A, sensor B, and prediction.
4. Reset sensor noise, move only process-acceleration uncertainty, and see rate gain and reported
   rate uncertainty change.
5. Explain both effects from `Q`, `R`, `S`, and `K` rather than from MATLAB syntax.
6. Inject one `+4 m` outlier and recognize a normalized-innovation-squared spike.
7. Remove the outlier, run deterministic checks, and give a two-sentence teach-back.

## Run

From MATLAB with the repository as the current folder:

```matlab
launch_lesson("P16")
moduleFolder = fullfile(pwd,"modules","16-fuse-noisy-sensors-with-a-kalman-filter");
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
run_module_checks("P16")
```

`launch_lesson` removes its temporary module path when the lesson returns. Add the folder only while
opening the interactive view, as shown, and remove it on both normal and error paths so generic
module-local function names cannot shadow another module later in the MATLAB session.

The model uses deterministic base MATLAB arithmetic and a local Park–Miller/Box–Muller generator;
it does not alter MATLAB's global random stream. The seeded pseudo-noise is a repeatable teaching
fixture, not sensor qualification. Retained evidence is static plus independent Python reference
simulation. No MATLAB-runtime, UI, MATLAB numerical-fidelity, bench, HIL, field, or production
validation is implied.
