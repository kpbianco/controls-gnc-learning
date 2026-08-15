# Walkthrough: Reject a Disturbance with Feedback

Run one experiment section per step so every changed view has one cause.

1. Read the guiding question: What inputs, observable effects, and failure modes matter when you reject a Disturbance with Feedback?
2. Recall P06's proportional offset and P07's loop reserve. Predict what larger
   feedback gain does to output deviation and control effort under a constant load.
3. Run only the baseline time section. Observe the unit disturbance, `0.2 output`
   residual, and `-0.8 output` controller effort for `K = 4`.
4. Reveal the frequency view. Compare absolute `|Y/D|` with and without feedback,
   then inspect the relative ratio so plant filtering is not credited to feedback.
5. Run sweep 1. Only feedback gain changes. Verify that residual output and loop
   time constant fall while steady controller effort approaches the load amplitude.
6. Reset `K = 4`, then run sweep 2. Only disturbance frequency changes. Observe
   smaller absolute fast-load output but a relative feedback benefit closer to one.
7. Open `interactive.m`. Move gain once, press **Reset baseline**, then move
   frequency once. Name the changed metric and the input that stayed fixed.
8. Run the broken sensor-bias case. Compare true output with measured output and
   name the violated honest-sensor assumption before viewing recovery.
9. Recover by validating and removing bias, not by increasing gain. Run
   `run_checks.m`, then answer `checks.md` one question at a time.
10. Teach back in two sentences: say where the load and bias enter, explain one
    rejection tradeoff, and identify the bias symptom plus recovery.
