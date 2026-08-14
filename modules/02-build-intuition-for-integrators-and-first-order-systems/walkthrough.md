# Walkthrough: Build Intuition for Integrators and First-Order Systems

Run one experiment section per step so each visual transition has one cause.

1. Read the guiding question: What inputs, observable effects, and failure modes matter when you build Intuition for Integrators and First-Order Systems?
2. Recall P01: damping made stored motion decay. Predict which P02 output can settle while a positive input remains applied.
3. Run only the baseline sections of `experiment.m`. On the output plot, the integrator is a straight ramp while the first-order response bends toward `K*A`.
4. Inspect the rate view. The integrator rate stays at `A`; the first-order rate begins at `K*A/tau` and shrinks with the equilibrium gap.
5. Run sweep 1. Only amplitude changes, so each integrator slope scales in direct proportion. Read the mechanism note before proceeding.
6. Reset to amplitude `A = 1`, then run sweep 2. Only `tau` changes; slower curves retain the same equilibrium. Each curve reaches 63.2% at its own `tau`.
7. Open `interactive.m`. Move amplitude once, press **Reset baseline**, then move `tau` once. State what changed and what remained invariant after each move.
8. Run the broken case. The exact curve still settles while explicit Euler alternates and grows. Name the violated interval-to-dynamics assumption, not merely “numerical error.”
9. Run `run_checks.m`, then answer `checks.md` one question at a time.
10. Teach back in two sentences: mechanism first, visible consequence second.
