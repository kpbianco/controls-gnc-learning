# P19 lesson: Measure Sensitivity to Model Error

## Guiding question

What inputs, observable effects, and failure modes matter when you measure Sensitivity to Model Error?

## Compounds on P18

P18 separated a known feedforward command from feedback correction. That lesson assumed the model
used by the reference and controller matched the plant. P19 keeps the same two command roles and
changes one physical coefficient at a time, so feedback's ability to reduce model error is measured
rather than assumed.

## Mental model

Imagine cruise control with a map that says how much throttle balances drag. The map is the nominal
model. A weak actuator or extra drag means the predicted speed and measured speed separate; feedback
responds to that gap, but a nonzero correction does not rewrite the map.

For the first-order speed plant and fixed controller,

```text
u[k]   = (a0/b0)*r[k] + K*(r[k]-v[k])
v[k+1] = exp(-a*dt)*v[k] + (b/a)*(1-exp(-a*dt))*u[k]
v_ss   = b*(a0/b0+K)*r / (a+b*K)
```

The speed and command are sampled every `dt=0.02 s`, and each command is held until the next sample.
The state update is the exact held-input solution of `dv/dt=-a*v+b*u`; the reported pole is for this
sampled-data feedback loop.

`a` is drag in `1/s`, `b` is dimensionless actuator effectiveness, speed is `m/s`, and command is
`m/s^2`. Differentiating the visible steady-state quotient gives output change per fractional model
change. At the matched baseline, the signs are opposite: more actuator gain raises steady speed,
while more drag lowers it.

## What the two levers reveal

- **Actuator gain ratio:** a weak actuator produces less speed per command. The actual controller asks
  for more correction, but the fixed proportional loop retains a steady prediction gap.
- **Drag ratio:** extra loss lowers speed for the same command. Because drag appears in the equilibrium
  denominator, its local sensitivity is negative.

At a ratio of one, predicted and actual histories are identical. The prediction gap is exactly zero,
yet the local sensitivities are not: zero present error does not mean zero vulnerability to the next
small parameter error.

## Deliberately broken assumption

Ordinary model uncertainty preserves the command direction. Reversed actuator polarity does not.
Positive tracking error then produces a command that drives actual speed farther from reference, the
discrete closed-loop pole magnitude exceeds one, and steady-response sensitivity is not meaningful
for the diverging trajectory. Restoring
the sign in a fresh call recovers the exact baseline because the model has no hidden state.

## Misconceptions to correct directly

- Sensitivity is not merely a large error; it is output change normalized by an input change.
- A zero baseline prediction gap does not prove the model is insensitive.
- Feedback attenuates these bounded errors but does not identify which physical parameter is wrong.
- Actuator error and drag error can have different signs even when their absolute sizes match.
- Reversed polarity is a violated structure, not a larger point on the positive-gain sweep.
- This lesson measures one fixed controller; choosing a robust design belongs to P20.
- Independent reference simulation is not MATLAB-runtime, UI, bench, HIL, or field evidence.

Ask one observation question at a time. Request the teach-back only after executable checks pass.
