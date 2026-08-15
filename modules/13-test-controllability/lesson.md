# P13 lesson: Test Controllability

## Guiding question

What inputs, observable effects, and failure modes matter when you test Controllability?

## Compounds on

P12 — Recover from Integrator Windup. P12 showed that an actuator may apply less effort than a
controller requests. P13 separates another issue: even before limits are imposed, the placement of
an input may leave a state direction unreachable.

## Mental model

Imagine a cart model with normalized position and rate coordinates. The actuator changes rate.
Position changes only because rate is coupled into the position equation. The two columns of
`[B, A*B]` ask:

- where does the input point immediately?
- where do the dynamics carry that input effect next?

Independent columns mean both normalized state directions are controllable. The finite-horizon
matrix in the experiment repeats the same idea for every held command sample and makes the target
transfer visible.

## What the two levers mean

- **Actuator effectiveness** scales how strongly every command sample enters the state. A weak but
  nonzero actuator can retain rank while demanding much more command energy.
- **Maneuver time** changes how many input effects can accumulate and flow from rate into position.
  More time can improve the weakest reachability direction and lower peak command.

Neither lever changes the target, damping, state scales, or the other lever during its sweep.

## Deliberately broken assumption

The broken case sets kinematic coupling to zero. Rate still answers a probe, so the actuator is not
dead, but position is frozen. The controllability rank falls from two to one and a position target
retains a one-metre terminal residual. That equality-constrained target has no minimum-energy
solution—effort is N/A, not zero. Restoring coupling recovers both rank and the transfer.

## Misconceptions to correct directly

- Full rank does not mean low effort, good conditioning, or compliance with an actuator limit.
- A small singular value is coordinate dependent; this lesson declares fixed state scales before
  comparing it.
- Controllability concerns whether input can move state. Whether a sensor can reveal state is the
  observability question in P14.
- `rank(ctrb(A,B))` is not the lesson. The governing columns, state effects, and failed assumption
  must remain visible.

Ask one observation question at a time, then request the teach-back only after executable checks.
