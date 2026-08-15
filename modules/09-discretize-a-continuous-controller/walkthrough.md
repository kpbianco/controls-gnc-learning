# P09 walkthrough: Discretize a Continuous Controller

Run one experiment section per step so every changed view has one cause.

1. Read the guiding question: What inputs, observable effects, and failure modes matter when you discretize a Continuous Controller?
2. Recall P06's integral memory and P08's continuous feedback loop. Predict whether
   sampling first appears as stair steps in plant output or control effort.
3. Run only the baseline output section. Compare the digital output with the stable
   continuous PI target for `Ts = 0.05 s` and backward Euler.
4. Reveal the held-effort section. Observe that command changes only at samples
   while the plant moves continuously between them. Read the baseline metrics.
5. Run sweep 1. Only sample period changes; keep backward Euler and both gains fixed.
   Watch the tracking gap and samples per natural period change.
6. Reset `Ts = 0.05 s`, then run sweep 2. Only the integration rule changes. Explain
   why current-error and previous-error memory updates produce different commands.
7. Open `interactive.m`. Move sample period once, press **Reset baseline**, then
   change the rule once. Name the metric that changed and what stayed fixed.
8. Run the broken `Ts = 0.8 s` forward-Euler case. First inspect pole magnitude,
   then reveal the growing oscillation and name the resolved-sampling assumption.
9. Recover by reducing `Ts` to `0.05 s`. Run `run_checks.m`, then answer
   `checks.md` one question at a time.
10. Teach back in two sentences: say what is sampled and held, explain one lever's
    effect, and identify the failure symptom plus recovery.
