# P19 checks: Measure Sensitivity to Model Error

Run `run_module_checks("P19")`, then answer one prompt at a time:

1. Why can the matched baseline have zero prediction gap but nonzero local sensitivities?
2. Why does a weaker actuator produce a negative steady prediction error while actuator-gain
   sensitivity is positive?
3. Why does extra drag have the opposite sensitivity sign from extra actuator effectiveness?
4. Which view distinguishes an ordinary positive actuator-gain error from reversed actuator polarity?
5. Why does feedback attenuate these parameter errors without proving which coefficient is wrong?

## Teach-back

In exactly two sentences, name the two uncertain inputs and the observable used to measure their
sensitivities. Then use the matched limit and reversed-sign pole to distinguish bounded model error
from a broken structural assumption.

The source and independent oracle provide static and simulated evidence only. No MATLAB-runtime,
rendered-UI, numerical-fidelity, bench, HIL, field, or production validation is claimed.
