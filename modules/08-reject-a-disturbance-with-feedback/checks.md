# P08 checks: Reject a Disturbance with Feedback

Run `run_checks.m` first. It checks determinism, governing equations, the exact
step and sinusoidal time histories, frequency limits, both isolated sweeps, the
sensor-bias failure and recovery, malformed inputs, numerical convergence, event
handling, and resource bounds. Then answer one interpretation question at a time.

1. A unit constant plant-input load produces `0.2 output` with `K = 4`. What
   equilibrium balance makes the remaining `-0.8 output` controller effort visible?
2. Why does increasing proportional gain reduce, but not eliminate, constant-load
   deviation? Which P06 mechanism could remove the residual?
3. A fast disturbance produces a smaller output but a with-feedback/no-feedback
   ratio closer to one. Which attenuation belongs to plant dynamics, and which
   belongs to feedback?
4. In the broken case, why can measured output approach zero while true output
   approaches minus the sensor bias as gain rises?
5. Why is sensor validation and correction the recovery, rather than another gain
   increase? How does P07 constrain any legitimate increase in loop action?

## Teach-back

In two sentences, name where a plant-input load and sensor bias enter, explain one
gain or frequency tradeoff, and identify the biased-sensor symptom and recovery.

Do not mark P08 complete until the executable checks pass and the learner gives
that teach-back. Static repository checks are not MATLAB-runtime, UI, numerical-
fidelity, bench, HIL, field, or production evidence.
