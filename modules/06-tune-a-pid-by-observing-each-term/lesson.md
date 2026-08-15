# P06 lesson: Tune a PID by Observing Each Term

## Guiding question

What inputs, observable effects, and failure modes matter when you tune a PID by Observing Each Term?

## Compounds on

P05 — Close a Loop with Proportional Control made `P = Kp*e` and finite
proportional offset visible. P06 keeps the measured-error loop, adds an error
memory and velocity damping, and uses a constant load so each term has a distinct
observable job.

## Mental model

The carriage obeys `m*x'' = u + Fload - b*x'` with `m = 1 kg`, `b = 0.5
N*s/m`, `r = 1 m`, and `Fload = -1 N`. The controller force is
`u = Kp*e + Ki*q - Kd*v`, where `e = r-x` and `q' = e`.

- Proportional action sees present error. It acts immediately, but on its own it
  must keep `0.25 m` of error so `Kp*e = 1 N` can balance the load.
- Integral action sees accumulated error. It can hold `+1 N` with nearly zero
  present error, but aggressive memory produces overshoot.
- Derivative action sees measured velocity. It vanishes at rest and trades force
  for damping during the transient.

The derivative is taken on measurement, not on the commanded step. For a constant
reference, `e' = -v`, so `D = -Kd*v`; this avoids presenting an ideal reference
step as an impulsive derivative force.

When `Ki = 0`, the carriage position can settle while the displayed error
accumulator keeps growing because it is disconnected from force. The module calls
that output loop stable but does not call the full integrated state asymptotically
stable.

## Tutor sequence

Ask one prediction: which term remains nonzero after error and velocity approach
zero? Show only the baseline position, then reveal the four force traces. Move
`Ki` once and explain offset versus stored-error overshoot. Reset, move `Kd` once,
and explain overshoot versus derivative effort. Finally reverse the derivative
sign and ask the learner to name the violated damping assumption from the growing
oscillation before showing recovery.

## Direct misconception corrections

- “Derivative removes steady error.” No. At rest `v = 0`, so D is zero; I supplies
  the steady load force.
- “Integral makes every response faster.” No. More integral action removes offset,
  but excess stored correction can overshoot and take longer to unwind.
- “Any oscillation means gains are merely high.” No. The broken case has a polarity
  error: `+Kd*v` reinforces motion. Restore the sign before tuning magnitudes.
- “The plot proves hardware behavior.” No. It is a deterministic software model;
  MATLAB runtime, UI, numerical fidelity, bench, HIL, and field behavior require
  separate evidence.

## Teach-back

In two sentences, name the input seen by P, I, and D; explain one visible `Ki` or
`Kd` tradeoff; then identify the wrong-sign derivative symptom and recovery.
