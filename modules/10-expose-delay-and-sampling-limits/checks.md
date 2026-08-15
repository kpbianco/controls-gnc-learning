# P10 checks: Expose Delay and Sampling Limits

Run `run_checks.m`, then answer one interpretation question at a time.

1. In the exact interval equation, what physical motion do `wOld` and `wNew` represent?
2. Why does the plant keep moving during computation delay?
3. In the sample-period sweep, what remains fixed and why does target gap increase?
4. In the delay sweep, what remains fixed and why does stale-command weight increase?
5. What should happen to the model as `Ts` and `Td` both approach zero?
6. What do the `Td=0` and `Td=Ts` limiting cases mean physically?
7. Why can Nyquist ratio above one coexist with an unstable feedback loop?
8. Which pole metric exposes the broken case before the time plot is trusted?
9. Why is reducing `Td` a real recovery while smoothing or interpolating samples is not?
10. Which retained numerical checks are independent of presentation plots?

## Teach-back

In two sentences, answer the guiding question by distinguishing `Ts` and `Td`, naming
one visible timing effect, and explaining the combined-limit failure plus recovery.

Do not mark personal completion until the executable checks pass and the learner
gives that teach-back. Static repository checks are not MATLAB-runtime, UI,
numerical-fidelity, bench, HIL, field, or production evidence.
