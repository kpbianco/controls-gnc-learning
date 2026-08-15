# P14 — Test Observability

**Track:** Controls, State Estimation, Guidance, and Navigation  
**Phase 4:** State-space control  
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you test Observability?

## Physical mental model

P13 asked whether an input can move every state direction. P14 turns the arrows around: can a
measurement history distinguish every possible initial state direction?

The concrete system has position and rate states with no commanded input during the observation
window:

```text
d(position)/dt = rate
d(rate)/dt     = -damping * rate
measurement    = sensor_gain * selected_state
```

A position sensor sees position immediately and reveals rate because rate changes future position.
The traditional two-state test stacks `O = [C; C*A]`. The experiment also stacks every exact sampled
output row over a finite window, so the learner can see which initial-state effects reach the sensor.

The state coordinates use fixed scales of `1 m` and `1 m/s`. Singular values and condition number are
therefore useful comparisons inside this lesson, but they remain coordinate-scaled diagnostics. Full
rank means a noise-free initial state is unique in this model; it does not promise acceptable sensor
noise, calibration, bias, or observer performance.

## Learning flow

1. Read the state and measurement equations and predict whether position history reveals rate.
2. Visualize two candidate initial states, their sensor histories, and baseline observability metrics.
3. Move only position-sensor sensitivity and observe output separation and noise amplification.
4. Reset sensitivity, move only observation-window duration, and observe accumulated rate evidence.
5. Explain both changes from the visible finite-window observation columns.
6. Measure rate only and recognize the identical-output, hidden-position-offset symptom.
7. Restore position measurement, run deterministic checks, and give a two-sentence teach-back.

## Run

From MATLAB with the repository as the current folder:

```matlab
launch_lesson("P14")
interactive
run_module_checks("P14")
```

The implementation uses deterministic base MATLAB arithmetic and no Control System Toolbox
observability, state-space, simulation, rank, or pseudoinverse helpers. A rank-deficient measurement
history is marked non-unique with its state estimate reported as N/A; it is not silently assigned a
zero estimate. Retained repository validation is static plus independent Python reference simulation.
No MATLAB-runtime, UI, MATLAB numerical-fidelity, bench, HIL, field, or production validation is
implied.
