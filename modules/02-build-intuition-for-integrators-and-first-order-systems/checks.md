# Checks: Build Intuition for Integrators and First-Order Systems

## Executable numerical checks

Run:

```matlab
run_checks
```

The assertions cover deterministic repeatability, analytic invariants, amplitude and
time-constant independence, zero-input and one-time-constant limits, the broken-Euler
symptom, malformed inputs, a strictly increasing endpoint-inclusive time grid, actual
Euler interval diagnostics, and the sample-count resource bound.

## Interpretation questions

1. Why does a constant positive input make the integrator ramp instead of settle?
2. When `tau` increases with `A` and `K` fixed, what changes in the first-order plot and what remains invariant?
3. At one time constant, what fraction of the first-order change is complete, and why is that not its final value?
4. In the broken case, which assumption is violated? Explain why the alternating growth is numerical rather than physical.
5. Connect this module to P01: which P01 effects resembled storage and which resembled a state losing its gap or energy?

## Teach-back

In two sentences, answer: “What inputs, observable effects, and failure modes matter
when you build Intuition for Integrators and First-Order Systems?” Lead with the two
mechanisms, then name their visible consequences and the coarse-step failure mode.
