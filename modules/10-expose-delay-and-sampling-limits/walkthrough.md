# P10 walkthrough: Expose Delay and Sampling Limits

Run one experiment section per step so every changed view has one cause.

1. Read the guiding question: What inputs, observable effects, and failure modes matter when you expose Delay and Sampling Limits?
2. Recall P05's proportional feedback and P09's sampled command. Predict whether
   computation delay first appears in applied command or plant output.
3. Run only the baseline output section for `Ts=0.05 s`, `Td=0.01 s`. Compare the
   timed loop with the immediate continuous proportional target.
4. Reveal computed versus applied commands. During `Td`, identify the previous
   command that remains active while the plant continues moving.
5. Run sweep 1. Keep `Td=0`, gain, plant, and reference fixed. Increase only `Ts`
   and observe continuous-target gap, overshoot, and pole magnitude.
6. Reset `Ts=0.1 s`, then run sweep 2. Increase only `Td` and connect the rising
   stale-command weight and delay phase to oscillation and overshoot.
7. Open `interactive.m`. Move sample period once, press **Reset baseline**, then
   move delay fraction once. Name what changed and what stayed fixed.
8. Inspect the broken `Ts=0.2 s`, `Td=0.18 s` pole magnitude and Nyquist ratio before
   revealing the growing time trace. State why Nyquist alone is insufficient.
9. Recover by reducing only `Td` to `0.02 s`. Run `run_checks.m`, then answer
   `checks.md` one question at a time.
10. Teach back in two sentences: distinguish sample spacing from compute latency,
    connect each lever to an observable, and name the failed assumption plus recovery.
