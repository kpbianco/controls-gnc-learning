# Walkthrough: Tune a PID by Observing Each Term

Run one experiment section per step so every changed view has one cause.

1. Read the guiding question: What inputs, observable effects, and failure modes matter when you tune a PID by Observing Each Term?
2. Recall P05's finite proportional offset, then predict which term will hold the
   carriage against `-1 N` after error and velocity approach zero.
3. Run only the baseline position section. Observe a bounded move from `0 m` toward
   the `1 m` reference and read final error, overshoot, settling time, and force.
4. Run the PID-term section. At `t = 0`, identify `P = 4 N`, `I = 0 N`, and `D =
   0 N`; near equilibrium, identify the integral term approaching `+1 N`.
5. Run sweep 1. Only `Ki` changes. Compare the `0.25 m` P+D offset at `Ki = 0`
   with offset removal and the larger overshoot at `Ki = 2 N/(m*s)`.
6. Reset `Ki = 1 N/(m*s)`, then run sweep 2. Only `Kd` changes. Compare position
   overshoot with peak derivative force while every other input stays fixed.
7. Open `interactive.m`. Move integral gain once, press **Reset baseline**, then
   move derivative gain once. State the changed observable and invariant each time.
8. Run the wrong-sign broken case. Name the violated derivative-damping assumption
   from the growing oscillation, then restore the opposing sign and observe recovery.
9. Run `run_checks.m`, then answer `checks.md` one question at a time.
10. Teach back in two sentences: say what P, I, and D observe, name a tuning
    tradeoff, and explain the wrong-sign symptom plus recovery.
