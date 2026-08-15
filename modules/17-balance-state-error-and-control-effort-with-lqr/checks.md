# P17 checks: Balance State Error and Control Effort with LQR

Run `run_module_checks("P17")` before answering the interpretation prompts.

## Observe

1. Why does raising `q_p` increase initial acceleration even though the initial state does not change?
2. Why does raising `r` reduce the squared-command effort integral but lengthen settling?
3. What normalization makes the terms in `J` compatible, and what physical units remain on the plots?
4. How does the Riccati matrix connect present state to future cost?
5. Why do stable nominal poles fail to move the cart when actual actuator effectiveness is zero?

## Numerical completion contract

The executable checks independently verify:

- the exact P16 zero-order-hold damped-cart matrices, cost definitions, Riccati recurrence, Bellman
  residual, feedback optimum, closed-loop characteristic equation, and every state transition;
- exact deterministic repeat, stable nominal poles, bounded baseline error/effort metrics, and
  separated physical units;
- isolated position-weight and effort-weight sweeps with their expected monotone tradeoffs;
- the zero-position-weight limiting case, disconnected-actuator symptom, unchanged design,
  exact fresh-call recovery, sign symmetry, and the largest accepted finite grid;
- nonscalar, nonreal, nonfinite, negative, zero, under-range, over-range, misaligned, under-resolved,
  and resource-exhausting inputs before state-history allocation.

## Teach back

In two sentences, answer: “What inputs, observable effects, and failure modes matter when you balance
State Error and Control Effort with LQR?” Name the state estimate, `Q`, `R`, and the actuator model;
describe one visible error/effort tradeoff; and explain the disconnected-actuator failure without
relying on MATLAB syntax.
