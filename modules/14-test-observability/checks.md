# P14 checks: Test Observability

Run `run_module_checks("P14")` before answering the interpretation prompts.

## Observe

1. Which initial state is visible in the first position sample, and which becomes visible only after
   the dynamics create later samples?
2. Why does halving sensor sensitivity increase inverse noise gain even though observability rank
   remains two?
3. Why does a longer observation window reveal initial rate more strongly without changing the
   sensor or dynamics?
4. In the broken case, why can the rate sensor produce a healthy signal while initial position
   remains ambiguous?

## Numerical completion contract

The executable checks independently verify:

- exact free-response state transition and traditional observability rows;
- every finite-window observation row and deterministic state recurrence;
- noise-free initial-state reconstruction from explicit two-by-two arithmetic;
- isolated sensor-sensitivity and observation-window sweeps;
- zero-sensor, rate-only, short-window, and zero-initial-rate limiting cases;
- malformed input, grid alignment, and resource bounds;
- isolation and recovery when position measurement is restored.

## Teach back

In two sentences, answer: “What inputs, observable effects, and failure modes matter when you test
Observability?” Name the measurement path, one visible output effect, and why full rank alone does
not guarantee a reliable estimate from an imperfect sensor.
