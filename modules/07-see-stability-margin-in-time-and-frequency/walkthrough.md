# Walkthrough: See Stability Margin in Time and Frequency

Run one experiment section per step so every changed view has one cause.

1. Read the guiding question: What inputs, observable effects, and failure modes matter when you see Stability Margin in Time and Frequency?
2. Recall P06's tuned closed-loop traces. Predict whether an actuator that falls
   behind the command adds or removes phase reserve.
3. Run only the baseline time section. Observe a bounded step with decaying
   oscillation and read overshoot plus settling time.
4. Run the baseline frequency section. At `omega_gc`, read magnitude `0 dB` and
   the angular distance from phase to `-180 deg`; connect that phase margin to
   the decay seen in time.
5. Run sweep 1. Only loop gain `K` (`1/s^2`) changes. Observe crossover move upward, phase
   margin shrink, and overshoot rise while actuator lag remains `0.2 s`.
6. Reset `K = 1`, then run sweep 2. Only actuator lag `tau` changes. Observe the
   extra phase lag and time ringing while gain remains invariant.
7. Open `interactive.m`. Move gain once, press **Reset baseline**, then move lag
   once. Name a changed observable and the held input each time.
8. Run the broken case. The instantaneous-actuator model looks bounded at `K =
   4 1/s^2`, but the actual `0.5 s` lag makes gain margin less than one and phase margin
   negative. Name the omitted-lag assumption from the growing response.
9. Recover by reducing gain below `Kcritical = 3` while retaining the `0.5 s`
   lag. Confirm that margins become positive and oscillations decay.
10. Run `run_checks`, answer `checks.md` one question at a time, and give the
    two-sentence teach-back.
