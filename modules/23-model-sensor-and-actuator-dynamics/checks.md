# P23 checks: Model Sensor and Actuator Dynamics

Run `run_module_checks("P23")`, then answer one prompt at a time:

1. Which inputs define command timing, actuator dynamics and authority, sensor dynamics and bias, and the
   bounded simulation grid? Include units.
2. Why does increasing sensor time constant leave the actual actuator history exactly unchanged?
3. Why does increasing actuator time constant affect both actual and measured acceleration but not the
   requested history?
4. How can you distinguish actuator saturation, dynamic lag, and sensor bias from their visible symptoms?
5. What does the zero-time-constant limit mean, and why does the equal-time-constant case need a finite
   repeated-pole expression?
6. In the broken case, why can measured acceleration retain the wrong sign even though the recurrence is
   stable and bounded?
7. What identification, calibration, timing, fault, bench, HIL, and field evidence is still required before
   using this model as a physical sensor or actuator claim?

## Teach-back

In exactly two sentences, name command half-period, actuator time constant, actuator limit, sensor time
constant, and sensor bias. Then explain how the two stored states create request-to-motion and
motion-to-measurement lag, and why fast reversals break the bandwidth-separation assumption.

The source and independent oracle provide static and simulated evidence only. No MATLAB-runtime,
rendered-UI, MATLAB numerical-fidelity, bench, HIL, field, or production validation is claimed.
