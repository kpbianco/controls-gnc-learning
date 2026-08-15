# P23 walkthrough: Model Sensor and Actuator Dynamics

## Learner sequence

1. Read the guiding question and P22 connection before running code.
2. Predict only which signal changes sign last after a baseline command reversal.
3. Visualize request, applied acceleration, and measured acceleration in `m/s^2`. Name their order without
   explaining it yet.
4. Visualize request-minus-applied and applied-minus-sensed errors. Identify where each error peaks.
5. Read the two first-order equations and connect each visible delay to its stored state and time constant.
6. Sweep only sensor time constant `[0 0.02 0.05 0.1 0.2 0.4] s`. Verify that command and actual actuator
   histories do not move while measurement error and stale-sign duration change.
7. Explain the changed view from `alpha_s=exp(-dt/tau_s)`, not from MATLAB plotting mechanics.
8. Reset sensor `tau_s=0.1 s`, then sweep only actuator time constant `[0 0.05 0.1 0.2 0.4 0.8] s`.
   Compare request-to-applied RMS error, peak applied acceleration, and downstream stale-sign time.
9. Explain why a sensor cannot report motion the actuator did not produce. Then distinguish time constant,
   magnitude limit, and sensor bias by the signal boundary each affects.
10. Run the broken `0.1 s` reversal case with actuator `tau_a=0.8 s` and sensor `tau_s=0.6 s`. Identify
    attenuated peaks and opposite-sign intervals, name the violated bandwidth-separation assumption, and
    restore the exact baseline.
11. Run `run_module_checks("P23")`, answer one interpretation prompt at a time, and give the required
    two-sentence teach-back.

No MATLAB-runtime, rendered-UI, calibration, actuator-characterization, bench, HIL, field, or physical
evidence is claimed by this walkthrough.
