# P20 checks: Compare Nominal and Robust Designs

Run `run_module_checks("P20")`, then answer one prompt at a time:

1. Why can the nominal design have smaller matched-plant ISE while the robust design has smaller
   worst-case ISE over the declared 25-point uncertainty grid?
2. What do the candidate set, 25-scenario grid, stability test, and command-effort limit each add to
   the meaning of “robust” here, and which reference, horizon, and sample interval bound that claim?
3. Why is the robust controller's exact zero steady error compatible with nonzero final error after
   a finite 12-second worst-corner run?
4. Which metrics expose the trade between tracking and command effort?
5. Why does reversed actuator polarity invalidate both designs' positive-gain evidence?

## Teach-back

In exactly two sentences, name the uncertain inputs, observable effects, and nominal-versus-robust
tradeoff. Then state the declared uncertainty boundary and explain the reversed-polarity symptom.

The source and independent oracle provide static and simulated evidence only. No MATLAB-runtime,
rendered-UI, numerical-fidelity, bench, HIL, field, or production validation is claimed.
