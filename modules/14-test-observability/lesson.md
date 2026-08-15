# P14 lesson: Test Observability

## Guiding question

What inputs, observable effects, and failure modes matter when you test Observability?

## Compounds on

P13 — Test Controllability. P13 followed command effects from an input into state directions. P14
uses the dual viewpoint: follow initial-state effects through the dynamics and out to a measurement.
The same state-space discipline applies, but reachability and visibility answer different questions.

## Mental model

Imagine a coasting cart with position and rate coordinates. Rate decays with drag, while position
accumulates rate. A position sensor directly reveals position; successive position samples reveal
the initial rate because different rates bend the position history differently. The rows of
`[C; C*A]` ask:

- what state combination does the sensor see immediately?
- what additional state combination reaches the sensor after the dynamics act?

Independent columns mean both normalized initial-state directions are observable. The finite-window
matrix in the experiment repeats the same idea at every sample and reconstructs the noise-free
initial state using explicit two-by-two arithmetic.

## What the two levers mean

- **Position-sensor sensitivity** scales every output effect. A weak but nonzero sensor can retain
  rank while shrinking candidate separation and increasing worst-case inverse noise gain.
- **Observation-window duration** controls how much position history is available. More time lets
  the initial rate accumulate into position and strengthens its weakest visible direction.

Neither lever changes damping, initial states, sample interval, sensor selection, state scales, or
the other lever during its sweep.

## Deliberately broken assumption

The broken case replaces position measurement with rate-only measurement. The sensor remains active,
but a constant initial-position offset never changes rate. Two trajectories one metre apart therefore
produce identical output histories. Observability rank falls from two to one and the model reports
the initial state as non-unique rather than inventing a zero position. Restoring position measurement
recovers output separation, full rank, and exact noise-free reconstruction.

## Misconceptions to correct directly

- Full rank does not mean good conditioning, adequate sensitivity, or immunity to noise and bias.
- A small singular value is coordinate dependent; this lesson declares fixed state scales before
  comparing it.
- Observability concerns whether outputs reveal state. Whether an input can move state was the
  controllability question in P13.
- `rank(obsv(A,C))` is not the lesson. The governing rows, output histories, ambiguous states, and
  failed measurement assumption must remain visible.

Ask one observation question at a time, then request the teach-back only after executable checks.
