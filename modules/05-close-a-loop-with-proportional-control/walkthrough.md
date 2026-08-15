# Walkthrough: Close a Loop with Proportional Control

Run one experiment section per step so every changed view has one cause.

1. Read the guiding question: What inputs, observable effects, and failure modes matter when you close a Loop with Proportional Control?
2. Recall P04's model-assumption boundary, then predict whether `Kp = 2` makes the output reach a `1 m` reference exactly.
3. Run only the baseline output section. Observe the quick rise and the gap that remains below the reference.
4. Run the error-and-effort section. Connect `u = Kp*e` to the fact that nonzero holding command requires nonzero error.
5. Run sweep 1. Only proportional gain changes; compare response time, final error, and initial command while plant time constant stays at `1 s`.
6. Reset `Kp = 2`, then run sweep 2. Only plant time constant changes; observe stretched transients and an unchanged steady-state ratio.
7. Open `interactive.m`. Move proportional gain once, press **Reset baseline**, then move plant time constant once. State the changed observable and invariant after each move.
8. Run the reversed-sign broken case. Name the violated subtracting-feedback assumption from the growing response, then restore negative feedback and observe recovery.
9. Run `run_checks.m`, then answer `checks.md` one question at a time.
10. Teach back in two sentences: state how measured error creates command, then name the gain tradeoff, reversed-sign symptom, and recovery.
