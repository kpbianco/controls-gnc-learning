# Walkthrough: Compare Linear and Nonlinear Pendulum Models

Run one experiment section per step so every changed view has one cause.

1. Read the guiding question: What inputs, observable effects, and failure modes matter when you compare Linear and Nonlinear Pendulum Models?
2. Recall P03's linear second-order motion and pole pair. Predict whether the nonlinear pendulum will lead or lag after a 20-degree release.
3. Run only the baseline motion section. Observe the initially close curves and the slowly accumulating timing difference.
4. Run the restoring-law section. Connect the weaker magnitude of `sin(theta)` away from zero to the nonlinear curve's later zero crossing.
5. Run sweep 1. Only release angle changes; compare five, 30, and 90 degrees while length, damping, and initial rate stay fixed. Read the mechanism note before proceeding.
6. Reset release angle to 20 degrees, then run sweep 2. Only length changes; connect the stretched cycles to `T_small = 2*pi*sqrt(L/g)`.
7. Open `interactive.m`. Move release angle once, press **Reset baseline**, then move length once. State the changed observable and invariant after each move.
8. Run the 120-degree broken case. Name the violated small-angle assumption from the early linear crossing, then observe recovery at five degrees.
9. Run `run_checks.m`, then answer `checks.md` one question at a time.
10. Teach back in two sentences: state the restoring-law mechanism first, then name when the approximation works, how failure appears, and how to recover.
