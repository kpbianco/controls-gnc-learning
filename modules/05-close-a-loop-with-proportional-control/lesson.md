# Lesson: Close a Loop with Proportional Control

## Guiding question

What inputs, observable effects, and failure modes matter when you close a Loop with Proportional Control?

## Compounds on P04

P04 showed that a calculation is useful only while its governing model and assumptions
match the question. P05 uses a transparent first-order plant rather than the pendulum
so one new mechanism can be isolated: the measured output changes the next command.
The pole-to-motion connection from earlier modules remains visible in the closed-loop
time scale.

## Mental model

Let `r` be a position reference in metres, `y` the measured position, `u` the
command, `G` the plant's static gain in metres per command unit, and `tau` its time
constant in seconds:

```text
plant:       tau*y' = -y + G*u
error:       e = r - y
controller:  u = Kp*e
closed loop: tau*y' = G*Kp*r - (1 + G*Kp)*y.
```

For negative feedback, the closed-loop pole is
`p = -(1 + G*Kp)/tau`. Increasing `Kp` moves that pole farther left and shortens
the time constant. At steady state, however,
`y_ss = G*Kp*r/(1 + G*Kp)` and `e_ss = r/(1 + G*Kp)`. The controller needs that
remaining error because `u_ss = Kp*e_ss` is what holds the plant away from zero.

## Observe before manipulating

Run only the baseline sections of `experiment.m`. Make one prediction: will the
output reach the `1 m` reference exactly with `Kp = 2`? Observe position first,
then inspect tracking error and command. Connect the residual error to the nonzero
command rather than calling it a numerical defect.

## Move one lever at a time

First sweep `Kp` while `tau = 1 s`. Larger gain makes the response faster and
reduces residual error, but it also increases the initial command. Reset `Kp = 2`,
then sweep only `tau`. A slower plant stretches the transient while leaving the
negative-feedback steady-state ratio unchanged.

## Deliberately broken assumption and recovery

Negative feedback assumes the measured output is subtracted. Reverse that sign and
the loop obeys `tau*y' = G*Kp*r + (G*Kp - 1)*y`. With `G*Kp > 1`, the pole is
positive: a positive output increases the command, which increases the output again.
The recognizable symptom is exponential growth away from the reference. Recover by
restoring the subtracting sign before changing gain. Saturation is intentionally not
added here; actuator constraints belong to a later module.

## Common misconceptions

- Closing a loop does not guarantee zero error. Proportional control alone needs
  steady error to produce a steady command for this plant.
- Larger `Kp` is not free: the initial and peak command grow even in this ideal model.
- Plant time constant changes transient speed, not the negative-feedback steady-state
  ratio for fixed `G` and `Kp`.
- Positive feedback is not simply “too much gain.” Its sign reverses correction into
  reinforcement; with `G*Kp > 1`, the closed-loop pole crosses into growth.
- A deterministic simulated curve is not hardware evidence, and this ideal model
  contains no sensor noise, delay, or actuator limit.

## Completion standard

Pass `run_checks.m`, answer the interpretation questions in `checks.md`, and give a
two-sentence teach-back: mechanism first, visible tradeoff and sign failure second.
MATLAB syntax is not an explanation.
