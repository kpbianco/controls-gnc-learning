# P11 checks: Drive an Actuator into Saturation

Run `run_checks.m`, then answer one interpretation question at a time.

1. Which two traces must be compared to prove saturation rather than infer it from output shape?
2. What physical quantity does `uRequested-uApplied` represent?
3. Why does the plant output remain continuous when the command is clipped?
4. In the reference sweep, what remains fixed and why does clipped time grow?
5. In the actuator-limit sweep, what remains fixed and why can low limits remain active?
6. What should happen when the actuator limit is high enough that the clamp never activates?
7. Why is the `r=1.5`, `uLimit=0.6` target infeasible for
   `tau*y'=-y+g*uApplied` with `g=1 output/actuator`?
8. Which retained invariant proves the actuator never exceeds its declared limit?
9. Why is increasing only the limit a real recovery while smoothing the plot is not?
10. Why is the integral absolute error metric in P11 not evidence of integrator windup?
11. Which numerical checks are independent of presentation plots?

## Teach-back

In two sentences, answer the guiding question by distinguishing reference demand from
actuator limit, naming one visible effect of clipping, and explaining persistent
saturation plus the one-limit recovery.

Do not mark personal completion until the executable checks pass and the learner gives
that teach-back. Static repository checks are not MATLAB-runtime, UI,
numerical-fidelity, bench, HIL, field, or production evidence.
