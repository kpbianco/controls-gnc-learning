# P22 walkthrough: Implement Proportional Navigation

## Learner sequence

1. Read the guiding question and P21 connection before running code.
2. Predict only whether the baseline LOS bearing will keep rotating or settle toward constant bearing.
3. Visualize engagement geometry first. Observe the interceptor curve toward the target path.
4. Visualize range and LOS rate. Identify decreasing range and LOS rate approaching zero before reading
   the mechanism.
5. Compare commanded and applied lateral acceleration against the `80 m/s^2` limit.
6. Sweep only `N = [1 2 3 4 5]` while target crossing speed, acceleration limit, step, and horizon reset.
   Observe that initial command scales with `N`, `N=1` misses, and stronger guidance captures.
7. Explain the changed view from `a_cmd=N*max(Vc,0)*lambdaDot`, not from MATLAB plotting mechanics.
8. Reset `N=3`, then sweep only acceleration authority `[5 10 20 40 80] m/s^2`. Compare closest range,
   peak applied acceleration, clipping duration, and intercept status.
9. Explain that the PN request and available vehicle turn are separate contracts.
10. Run the broken `5 m/s^2` case. Identify sustained clipping, closest approach outside the capture
    radius, opening range, and time-limit termination; then restore the exact baseline.
11. Run `run_module_checks("P22")`, answer one interpretation prompt at a time, and give the required
    two-sentence teach-back.

No MATLAB-runtime, rendered-UI, autopilot, actuator-dynamics, bench, HIL, field, or physical evidence is
claimed by this walkthrough.
