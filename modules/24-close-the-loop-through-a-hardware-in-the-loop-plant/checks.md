# P24 checks: Close the Loop Through a Hardware-in-the-Loop Plant

Run `run_module_checks("P24")`, then answer one prompt at a time:

1. Which inputs define the controller clock, both transport paths, command-age policy, deterministic loss,
   cancellation, virtual plant, and bounded grid? Include units.
2. Why does increasing one-way latency change measurement age without changing controller release times or
   the plant equation?
3. Why does increasing controller period reduce command count even though the plant tick remains fixed?
4. From the plots alone, how can you distinguish computed force, delivered force, a dropped command, an
   age-triggered watchdog interval, and explicit cancellation?
5. What does the zero-latency limiting case do at a controller tick, and why must cancellation be evaluated
   before a command due on the same tick?
6. In the broken case, why does dropping every second command interact with `T_c=0.1 s` and `T_w=0.12 s`
   to create safe-zero intervals?
7. What clock synchronization, serialization, endianness, transport, deadline, scheduling, electrical,
   actuator, sensor, emergency-stop, fault-injection, bench, and physical HIL evidence is still required?

## Teach-back

In exactly two sentences, name controller period, one-way latency, measurement timestamp, command age, and
watchdog timeout. Then explain how loss or cancellation changes applied force and why this deterministic
virtual-time loop is not physical HIL validation.

The source checks and independent oracle provide static and simulated evidence only. No MATLAB-runtime,
rendered-UI, MATLAB numerical-fidelity, external-protocol, bench, physical HIL, field, or production
validation is claimed.
