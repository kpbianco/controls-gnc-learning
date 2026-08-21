# P24 walkthrough: Close the Loop Through a Hardware-in-the-Loop Plant

## Learner sequence

1. Read the guiding question and P23 connection before running code.
2. Predict only which baseline view changes first when one-way latency grows: timestamp age, applied force,
   or mechanical position.
3. Visualize reference and virtual plant position in metres. Name the baseline tracking transition without
   explaining it yet.
4. Visualize measurement age in seconds and requested versus applied force in newtons. Identify the first
   interval where transport separates the two force signals.
5. Read the packet event order and exact mass–damper transition. Explain why the plant keeps moving while a
   measurement or command is in flight.
6. Sweep only one-way latency `[0.01 0.02 0.04 0.06 0.08] s`. Observe timestamp age first, then tracking
   RMS and peak position.
7. Reset latency to `0.01 s`, sweep only controller period `[0.02 0.04 0.05 0.1 0.2] s`, and observe fewer
   command packets, older held measurements, and the coarsest loop's changed response.
8. Explain why the second sweep did not change the `0.01 s` plant integration tick.
9. Run the broken `0.1 s` controller, `0.04 s` latency, `0.12 s` watchdog, drop-every-second-command case.
   Identify a dropped command, its stale interval, and the later safe-zero state as separate transitions.
10. Remove only the drop cadence and verify recovery. Then cancel at `4.01 s` as the command sourced at
    `4 s` is due, verify same-tick queued work is purged, and compare that explicit cancellation with an
    age-triggered timeout.
11. Run `run_module_checks("P24")`, answer one interpretation prompt at a time, and give the required
    two-sentence teach-back.

No MATLAB-runtime, rendered-UI, wall-clock, external-protocol, target, bench, physical HIL, field, or
production evidence is claimed by this walkthrough.
