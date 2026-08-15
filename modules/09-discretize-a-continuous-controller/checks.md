# P09 checks: Discretize a Continuous Controller

Run `run_checks.m`, then answer one interpretation question at a time.

1. In `y[k+1] = a*y[k] + (1-a)*u[k]`, what does `a = exp(-Ts)` mean physically?
2. Which signal is sampled, which command is held, and why is plant output not a staircase?
3. In the sample-period sweep, what remains fixed and why does the continuous-target gap grow?
4. In the rule sweep, which error sample enters forward versus backward Euler memory?
5. What limiting behavior should both rules approach as `Ts` tends toward zero?
6. Why can a stable continuous PI target produce an unstable discrete realization?
7. In the broken case, which pole metric exposes failure before the plot is trusted?
8. Why is reducing sample period a valid recovery while drawing a smooth interpolation is not?
9. Which retained checks are independent of the presentation plots?

## Teach-back

In two sentences, answer the guiding question by naming the timing inputs, one
observable discretization effect, and the coarse-sampling failure plus recovery.

Do not mark personal completion until the executable checks pass and the learner
gives that teach-back. Static repository checks are not MATLAB-runtime, UI,
numerical-fidelity, bench, HIL, field, or production evidence.
