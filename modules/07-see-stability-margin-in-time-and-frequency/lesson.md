# P07 lesson: See Stability Margin in Time and Frequency

## Guiding question

What inputs, observable effects, and failure modes matter when you see Stability Margin in Time and Frequency?

## Compounds on

P06 — Tune a PID by Observing Each Term showed that a controller can look well
tuned for one model. P07 steps outside the closed-loop trace and measures how much
gain and phase change that design can tolerate.

## Mental model

The plant has one integrating state and one damped state. Normalized output `y`
has unit `output`; `v` has `output/s`; the plant damping rate is `b = 1/s`; and
controller gain `K` has `1/s^2`. The command `c = K(r-y)`, in `output/s^2`,
passes through an actuator with time constant `tau` before becoming plant
acceleration `a`:

- `y' = v`;
- `v' = a-b*v`;
- `tau*a' = c-a` when `tau > 0`.

Opening the loop gives `L(s) = K/[s(s+b)(tau*s+1)]`. At frequency `omega`, its
magnitude and phase are evaluated factor by factor:

- `|L(j*omega)| = K/[omega*sqrt(b^2+omega^2)*sqrt(1+(tau*omega)^2)]`;
- `angle L = -90 deg - atan(omega/b) - atan(tau*omega)`.

Gain crossover `omega_gc` is where magnitude equals one. Phase margin is the
distance from the phase there to `-180 deg`. For positive actuator lag, phase
crossover is independently `sqrt(b/tau)`, critical gain is
`b*(1+b*tau)/tau` in `1/s^2`, and gain margin is the dimensionless ratio
`Kcritical/K`.

That reserve is not a cosmetic frequency-domain number. Increasing `K` moves
crossover upward, where both dynamic factors contribute more lag. Increasing
`tau` makes the actuator fall behind at a lower frequency. Either change reduces
margin, so the time response rings more. Crossing zero phase margin makes a mode
grow instead of decay.

## Tutor sequence

Ask one prediction: will added actuator lag increase or decrease the reserve?
Show only the baseline time response. Then reveal magnitude and phase at the
marked gain crossover. Move `K` once and connect crossover, margin, and overshoot.
Reset, move `tau` once, and identify the same mechanism without changing gain.
Finally compare the instantaneous-actuator prediction with the broken lagged
loop. Ask for the violated assumption before showing gain reduction as recovery.

## Direct misconception corrections

- “A positive gain margin means no oscillation.” No. It means the loop can
  tolerate some gain increase before instability; a stable loop can still ring.
- “Gain crossover is a closed-loop natural frequency.” No. It is the open-loop
  unity-magnitude frequency, used here to measure phase reserve.
- “Actuator lag only makes the response slower.” No. It also subtracts phase near
  crossover and can turn decaying oscillation into growth.
- “The Bode view is a separate model.” No. Its factors come from the same state
  equations used by the time calculation.
- “These plots prove hardware margins.” No. They are retained static and
  deterministic software artifacts; runtime and physical claims need separate
  evidence.

## Teach-back

In two sentences, name the two levers, connect one frequency-margin change to one
time-domain symptom, then identify the broken actuator assumption and recovery.
