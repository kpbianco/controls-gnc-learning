# P15 checks: Build a State Observer

Run `run_module_checks("P15")` before answering the interpretation prompts.

## Observe

1. How does position innovation correct rate when the observer never receives a rate measurement?
2. Why does increasing pole speed reduce fixed-horizon baseline error while increasing correction gain?
3. Why does deterministic position-sensor interference create both position- and rate-estimate ripple?
4. In the broken case, why can innovation approach zero while the position estimate remains wrong?
5. Which observer inputs must match or be trustworthy: model, known command, measurement calibration,
   initial estimate, or correction gain?

## Numerical completion contract

The executable checks independently verify:

- exact zero-order-hold plant matrices and hand-derived repeated observer-pole gain;
- error-transition trace, determinant, Jordan identity, and every sampled recurrence;
- matched known-input cancellation and the exact-initial-estimate limiting case;
- isolated pole-speed and deterministic measurement-interference sweeps;
- linear interference response, biased-sensor false confidence, fresh-call recovery, and zero-command limit;
- malformed input, grid alignment, and resource bounds before history allocation.

## Teach back

In two sentences, answer: “What inputs, observable effects, and failure modes matter when you build a
State Observer?” Name the prediction inputs and innovation, one visible speed-versus-interference
tradeoff, and why observability plus quiet innovation cannot protect against sensor bias.
