# P21 walkthrough: Generate a Feasible Trajectory

## Learner sequence

1. Read the guiding question and P20 connection before running code.
2. Predict only whether the `20 m` in `8 s` baseline fits `5 m/s` and `2 m/s^2` limits.
3. Visualize position and speed first. Observe zero endpoint speed and the midpoint peak.
4. Visualize acceleration and constraint bands. Compare analytic peaks, utilization, and minimum duration.
5. Sweep only target distance while duration and both limits remain at baseline. Observe demands grow
   linearly and identify where the active minimum-duration constraint changes.
6. Explain that a longer distance applies the same normalized shape over more metres.
7. Reset distance to `20 m`, then sweep only duration. Observe peak speed scale as `1/T`, acceleration as
   `1/T^2`, and jerk as `1/T^3`.
8. Explain the changed view from the chain rule and time scaling, not from MATLAB plotting mechanics.
9. Run the `4 s` broken request. Identify both violated constraints even though endpoint conditions and
   smoothness remain intact, then restore the `8 s` baseline.
10. Run `run_module_checks("P21")`, answer one interpretation prompt at a time, and give the required
    two-sentence teach-back.

No MATLAB-runtime, rendered-UI, plant-tracking, HIL, or physical evidence is claimed by this walkthrough.
