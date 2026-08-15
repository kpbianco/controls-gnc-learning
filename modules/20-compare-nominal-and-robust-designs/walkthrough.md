# P20 walkthrough: Compare Nominal and Robust Designs

## Learner sequence

1. Read the guiding question and P19 plant recurrence before running code.
2. Predict only which design has smaller tracking ISE on the exactly matched plant.
3. Visualize baseline speed and command. Observe the nominal design's faster matched response and
   compare tracking ISE with command-effort integral.
4. Read the finite selection table: 12 PI candidates, 25 positive plant scenarios, stability on
   every scenario, and a `90 m^2/s^3` worst-effort limit for a `1 m/s` step, 12-second horizon,
   and `dt=0.02 s`. Other reference amplitudes are exploratory.
5. Sweep only actuator gain ratio while drag stays one. Compare both designs' ISE and final error.
6. Explain the changed view from command effectiveness and integral correction, not from MATLAB
   syntax or the word “robust.”
7. Reset actuator gain to one and sweep only drag. Observe how extra loss changes both finite-time
   tracking and required steady command.
8. Explain why the nominal feedforward is exact only when the model ratio matches and why stable PI
   has zero asymptotic error even though its finite-horizon final error remains visible.
9. Reverse actuator polarity. Identify pole magnitude above one and bounded early termination as a
   structural failure outside the positive design grid, then restore positive polarity.
10. Run `run_module_checks("P20")`, answer one interpretation prompt at a time, and give the required
    two-sentence teach-back.

No MATLAB-runtime, rendered-UI, or physical evidence is claimed by this source walkthrough.
