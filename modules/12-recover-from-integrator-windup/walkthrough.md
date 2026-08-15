# P12 walkthrough: Recover from Integrator Windup

## Read

Read the guiding question and the two integral-state equations in `README.md`. Recall from P11 that
the command gap is requested effort minus applied effort. Predict once which loop reverses applied
control first when the target changes sign.

## Baseline

Run the first four sections of `experiment.m`.

1. In the output view, both paths initially rise under the same `+1 actuator` clamp.
2. At `3 s`, the reference changes from `+2` to `-0.5 output`.
3. The protected path turns its applied command negative immediately; the unprotected path retains
   a positive integral state near `3.95 actuator` and delays reversal by about `2.02 s`.
4. The protected path has lower post-release integral absolute error.

Mechanism: the negative correction `Kaw*(uApplied-uRequested)` acted while positive command was
missing. It reduced controller memory before the target changed.

## Lever 1 — anti-windup gain

Run the `Kaw` sweep while demand duration remains `3 s`.

- At `Kaw=0`, protected and unprotected paths coincide exactly.
- Moderate correction reduces stored positive state and recovery error.
- Larger values can push release state negative; observe that recovery quality is not monotonic.

Read the explanation only after comparing the output and metric views.

## Lever 2 — high-demand duration

Reset `Kaw=1 1/s`, then run the duration sweep.

- The unprotected integral state at reversal grows with every longer high-demand interval.
- Its post-release error also grows.
- The protected release state and error stay bounded because the command gap is fed back during
  saturation.

Duration changes how long windup can accumulate. It does not change actuator limit, PI gains, plant,
or time-step mechanics.

## Broken case and recovery

Run the wrong-sign section.

1. The broken integral state grows rapidly because unavailable command reinforces itself.
2. After the reference reverses, applied control remains positive and output stays on the wrong side.
3. Restore the sign to `+1`; the correction drains unavailable effort and recovery resumes.

## Check and teach back

Run `run_module_checks("P12")`. Answer the interpretation questions in `checks.md`, then give the
two-sentence teach-back. Personal completion is separate from batch implementation and should be
recorded only after the executable checks and teach-back.
