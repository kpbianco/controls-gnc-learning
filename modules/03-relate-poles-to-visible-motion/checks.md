# P03 checks: Relate Poles to Visible Motion

Run `run_checks.m` first. It checks deterministic repeatability, initial conditions,
the characteristic equation, analytic envelope bounds, energy direction, lever
independence, repeated and marginal limits, the broken/recovered pair, malformed
inputs, endpoint behavior, and calculation resource bounds.

Then answer one interpretation question at a time:

1. With `sigma = -0.5 1/s` and `omega = 2 rad/s`, which visible feature comes from each coordinate, and what are the envelope time constant and oscillation period?
2. When only `sigma` becomes more negative, why does the motion disappear sooner even though its zero-crossing spacing remains similar?
3. When only `omega` increases, why do more cycles fit in the same window without changing the common exponential ratio?
4. What happens at the two limits `sigma = 0` and `omega = 0`, and how does the double-zero case reconnect to P02's integrator?
5. In the broken case, which assumption is violated, what symptoms reveal it, and what single coordinate change recovers decay?

## Teach-back

In two sentences, answer: “What inputs, observable effects, and failure modes matter
when you relate Poles to Visible Motion?” Sentence one must map real and imaginary
coordinates to mechanisms. Sentence two must connect initial conditions to visible
motion and explain the right-half-plane failure plus its recovery.

Passing static repository tests does not claim that these MATLAB checks, figures, or
controls executed. Record a separate MATLAB-runtime result if they are run.
