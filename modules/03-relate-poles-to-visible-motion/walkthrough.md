# Walkthrough: Relate Poles to Visible Motion

Run one experiment section per step so every changed view has one cause.

1. Read the guiding question: What inputs, observable effects, and failure modes matter when you relate Poles to Visible Motion?
2. Recall P02's first-order pole at `-1/tau`. Predict whether the P03 baseline will reverse direction and whether its envelope will grow or shrink.
3. Run only the baseline motion section. Observe repeated zero crossings inside the shrinking displacement envelope.
4. Run the pole-plane section. Connect horizontal coordinate `sigma = -0.5 1/s` to decay and vertical coordinates `+/-2 rad/s` to the `pi`-second period.
5. Run sweep 1. Only `sigma` changes, so the envelope constants become 1, 2, and 5 seconds while cycle spacing stays fixed. Read the mechanism note before proceeding.
6. Reset `sigma = -0.5 1/s`, then run sweep 2. Only `omega` changes, so periods become `2*pi`, `pi`, and `pi/2` seconds while the exponential ratio stays fixed.
7. Open `interactive.m`. Move the real coordinate once, press **Reset baseline**, then move the imaginary coordinate once. State the changed observable and invariant after each move.
8. Run the broken case. Identify the violated left-half-plane/dissipation assumption from the growing envelope and energy, then explain why restoring negative `sigma` recovers decay.
9. Run `run_checks.m`, then answer `checks.md` one question at a time.
10. Teach back in two sentences: map pole coordinates to mechanisms first, then name their visible consequences and the right-half-plane failure.
