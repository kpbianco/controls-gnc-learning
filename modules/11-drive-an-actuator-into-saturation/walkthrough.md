# P11 walkthrough: Drive an Actuator into Saturation

1. Read the guiding question and predict where clipping appears first.
2. Run the `r=1 output`, `uLimit=2 actuator` baseline output section. The limited
   response initially trails the unlimited proportional response, then approaches the
   same P-only equilibrium.
3. Reveal the command view. The controller initially requests `4 actuator`, the plant
   receives `2 actuator`, and the clipping gap is `2 actuator`.
4. Observe that clipping releases near `0.29 s`; requested and applied commands then meet.
5. Sweep only reference through `[0.25 0.5 1 1.5 2] output` at a fixed `2 actuator`
   limit. Larger demand widens the missing-command gap and increases clipped time.
6. Reset reference to `1 output`. Sweep only limit through
   `[0.4 0.6 0.8 1.2 2] actuator`. Low authority keeps the command clipped; higher
   authority releases sooner and reduces accumulated absolute tracking error.
7. Run the broken `r=1.5`, `uLimit=0.6` case. The actuator remains at its limit and
   the output approaches `0.6`, not the requested `1.5`.
8. Increase only the limit to `2 actuator`. The command releases from saturation and
   the trajectory recovers toward the unchanged P-only equilibrium.
9. Explain the mechanism: the clamp bounds applied effort, and plant gain
   `g=1 output/actuator` converts that bounded effort into visible motion.
10. Run `run_checks.m` and give the teach-back from `checks.md`.

Do not describe static checks as MATLAB execution. No rendered plot, UI callback,
MATLAB numerical-fidelity, bench, HIL, field, or production result is retained here.
