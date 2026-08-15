# P13 checks: Test Controllability

Run `run_module_checks("P13")` before answering the interpretation prompts.

## Observe

1. In the baseline probe view, which state responds directly to command, and which state responds
   only after the kinematic coupling acts?
2. Why does halving actuator effectiveness increase command-energy demand even though the
   controllability rank remains two?
3. Why does a longer maneuver need less peak command without changing `A`, `B`, damping, target, or
   sample interval?
4. In the broken case, why can rate respond to a probe while position remains frozen?

## Numerical completion contract

The executable checks independently verify:

- exact zero-order-held state and input matrices;
- traditional and finite-horizon controllability identities;
- deterministic state recurrences and target reconstruction;
- isolated actuator-effectiveness and maneuver-time sweeps;
- zero-input and disconnected-coupling limiting cases;
- malformed input, grid alignment, response, and resource bounds;
- recovery when the missing coupling is restored.

## Teach back

In two sentences, answer: “What inputs, observable effects, and failure modes matter when you test
Controllability?” Name the input path, one visible state effect, and why full rank alone does not
guarantee a physically feasible maneuver.
