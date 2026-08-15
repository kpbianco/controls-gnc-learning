# P16 checks: Fuse Noisy Sensors with a Kalman Filter

Run `run_module_checks("P16")` before answering the interpretation prompts.

## Observe

1. Why does raising sensor A's reported noise lower its gain even though the raw seeded sensor data
   do not change?
2. Why does raising process uncertainty increase rate correction from position innovations?
3. What units belong to `Q`, `R`, the two innovations, the gain entries, and NIS?
4. Why can two individually noisy position sensors reconstruct rate when neither measures rate?
5. In the broken case, why does NIS spike, and why does that diagnostic not reject the outlier by itself?

## Numerical completion contract

The executable checks independently verify:

- the exact P15 zero-order-hold plant matrices and covariance definitions;
- the local seeded noise sequence, deterministic repeat, truth, predict, gain, update, Joseph
  covariance, and NIS recurrences at every sample;
- covariance symmetry, positive diagonals and determinant, separated position/rate units, and bounded
  baseline metrics;
- isolated sensor-noise and process-noise sweeps with their monotone gain/covariance consequences;
- a single-sample outlier symptom, unchanged truth and gain, exact fresh-call recovery, alternate-seed
  isolation, and the largest accepted finite grid;
- nonscalar, nonreal, nonfinite, nonpositive, noninteger, under-range, over-range, misaligned, and
  resource-exhausting inputs before trajectory allocation.

## Teach back

In two sentences, answer: “What inputs, observable effects, and failure modes matter when you fuse
Noisy Sensors with a Kalman Filter?” Name prediction, two measurements, `Q`, and `R`; describe one
visible trust tradeoff; and explain the outlier/NIS failure without relying on MATLAB syntax.
