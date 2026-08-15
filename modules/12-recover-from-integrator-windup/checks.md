# P12 checks: Recover from Integrator Windup

Run from MATLAB:

```matlab
run_module_checks("P12")
```

The executable checks cover deterministic repeatability, the explicit clamp, exact held-input plant
motion, both integral-state recurrences, event-aligned and partial time intervals, the `Kaw=0`
limiting case, both independent sweeps, wrong-sign failure and recovery, malformed inputs, and
sample/response resource bounds.

## Interpretation questions

1. During positive saturation, why is `uApplied-uRequested` negative, and what should that do to a
   positive integral state?
2. Why do protected and unprotected paths coincide exactly when `Kaw=0`?
3. Why can longer high-demand duration worsen unprotected recovery without changing the plant?
4. Why can excessive correction gain produce a different recovery penalty even though it prevents
   positive windup?
5. What output, integral-state, and applied-command symptoms identify the wrong-sign broken case?

## Teach-back

In two sentences, answer the guiding question: explain the inputs that control windup recovery, the
observable effects of stored integral effort, and the failure caused by reversing the command-gap
feedback sign. Mention that anti-windup changes controller memory, not actuator authority.
