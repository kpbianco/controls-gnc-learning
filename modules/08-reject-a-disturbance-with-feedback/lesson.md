# P08 lesson: Reject a Disturbance with Feedback

## Guiding question

What inputs, observable effects, and failure modes matter when you reject a Disturbance with Feedback?

## Compounds on

P06 made proportional offset, integral memory, and controller effort visible.
P07 connected loop gain to stability reserve. P08 keeps a stable transparent
loop and asks what unwanted input enters, what signal feedback observes, and what
tradeoff is visible when gain changes.

## Mental model

The normalized plant is `tau*y' = -y + u + d`, with `tau = 1 s`, zero reference,
and `u = -K*y_m`. Output `y`, plant-input disturbance `d`, measurement bias, and
control effort `u` share normalized `output` units. Gain is dimensionless.

For an honest sensor, `y_m = y`. A constant load then settles at
`y_ss = d/(1+K)` while the controller holds `u_ss = -K*d/(1+K)`. More gain reduces
the residual and shortens the loop time constant to `tau/(1+K)`, but controller
effort approaches the full load. Proportional feedback does not make a constant
residual exactly zero; P06's integral term is the mechanism for that job.

For a sinusoidal load, the exact disturbance-to-output magnitude is
`1/sqrt((1+K)^2 + (tau*omega)^2)`. The plant itself filters fast inputs. The
relative with-feedback/no-feedback ratio approaches `1/(1+K)` at low frequency
but approaches one at high frequency. A small fast output does not mean feedback
did all the work.

The broken case uses `y_m = y + b`. With no physical load, equilibrium becomes
`y = -K*b/(1+K)` and `y_m = b/(1+K)`. High gain can make the measured error look
small by moving the true plant almost one bias unit in the opposite direction.
That is a disturbance-location failure, not inadequate gain.

## Tutor sequence

Ask one prediction: as gain rises against a constant plant-input load, which gets
smaller—true output, controller effort, or both? Show the baseline output first,
then reveal effort. Move gain once and explain the equilibrium balance. Reset and
move disturbance frequency once; separate absolute plant filtering from feedback's
additional rejection. Finally inject sensor bias, ask which signal looks healthy,
and recover by validating and correcting the sensor.

## Direct misconception corrections

- “Feedback removes any disturbance.” No. Rejection depends on where the input
  enters and what the controller measures.
- “A small high-frequency response proves strong feedback.” No. The uncontrolled
  first-order plant already filters fast inputs; compare the relative ratio.
- “More proportional gain removes a constant load completely.” No. Finite gain
  leaves `d/(1+K)` so it can command the holding effort.
- “A near-zero sensor reading proves true output is near zero.” No. Bias can make
  the loop move the plant while hiding that motion in the measurement.
- “The plot proves hardware behavior.” No. It is a deterministic software model;
  MATLAB runtime, UI, numerical fidelity, bench, HIL, and field behavior require
  separate evidence.

## Teach-back

In two sentences, name the plant-input disturbance and measured signal, explain
one gain or frequency tradeoff, then identify the sensor-bias symptom and recovery.
