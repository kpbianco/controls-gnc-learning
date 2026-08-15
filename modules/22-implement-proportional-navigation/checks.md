# P22 checks: Implement Proportional Navigation

Run `run_module_checks("P22")`, then answer one prompt at a time:

1. How do relative position and velocity produce range, closing speed, and LOS rate, including their units?
2. Why does constant bearing plus decreasing range indicate intercept, while small range by itself does not?
3. What does `N` change immediately, and why can increasing it raise acceleration demand?
4. Why can the raw PN command be correct while an acceleration-limited vehicle still misses?
5. What observable distinguishes the `5 m/s^2` broken case from the `80 m/s^2` baseline?
6. Why must capture be checked between time samples, and why is capture-radius entry not exact collision?
7. What sensor, delay, actuator, autopilot, target-maneuver, HIL, and field evidence is still required before
   transferring this result to a physical vehicle?

## Teach-back

In exactly two sentences, name `r`, `v_rel`, `Vc`, `lambdaDot`, `N`, and acceleration authority. Then explain
the visible constant-bearing/decreasing-range mechanism and why sustained command clipping causes the broken
case to miss.

The source and independent oracle provide static and simulated evidence only. No MATLAB-runtime,
rendered-UI, MATLAB numerical-fidelity, autopilot, bench, HIL, field, or production validation is claimed.
