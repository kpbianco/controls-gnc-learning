# P18 checks: Use Feedforward and Feedback Together

Run `run_module_checks("P18")`, then answer one prompt at a time:

1. Before the load pulse, why can matched feedforward move the cart with zero feedback correction?
2. When `alpha=0`, what signal must appear before feedback can recreate the planned input?
3. Why does `beta=0` leave a position offset after a finite disturbance even though feedforward still
   follows the nominal plan?
4. Which plot distinguishes a reversed feedforward convention from an unexpectedly large disturbance?
5. Why can the total-command squared integral be smaller than the sum of the two component integrals?

## Teach-back

In exactly two sentences, state what information feedforward uses and what observable feedback uses.
Then explain how the baseline, one limiting case, and the reversed-sign symptom show why the two paths
belong together.

The source and independent oracle provide static and simulated evidence only. No MATLAB-runtime,
rendered-UI, numerical-fidelity, bench, HIL, field, or production validation is claimed.
