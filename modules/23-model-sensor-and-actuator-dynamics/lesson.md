# P23 lesson: Model Sensor and Actuator Dynamics

## Guiding question

What inputs, observable effects, and failure modes matter when you model Sensor and Actuator Dynamics?

## Compounds on P22

P22 turned relative position and line-of-sight rate into a lateral-acceleration request, then clipped that
request to idealized acceleration authority. P23 makes the next boundary explicit: a guidance request is an
input to an actuator, the actuator's applied motion is an input to a sensor, and the sensor report can lag
or differ from both. This module does not rerun the P22 engagement or claim an autopilot.

## Mental model and visible equations

Think of the actuator and sensor as two memories in series. Over a held-input interval, each time constant
decides how much old state remains:

```text
u_limited = clip(u, -a_max, +a_max)                 [m/s^2]
tau_a * da/dt + a = u_limited                       [s, m/s^2]
tau_s * dy/dt + y = a                               [s, m/s^2]
y_reported = y + bias                               [m/s^2]
alpha = exp(-dt/tau)                                [dimensionless]
```

A larger time constant makes `alpha` closer to one, preserving more old state. The exact source recurrence
keeps the governing operation visible and handles zero time constants as ideal devices. Equal positive
time constants use the finite repeated-pole limit rather than dividing by nearly zero.

## What the baseline reveals

The request alternates between `+20` and `-20 m/s^2` every `2 s`. With actuator `tau_a=0.2 s` and sensor
`tau_s=0.1 s`, applied acceleration moves first and the sensor report follows. Neither device changes
instantly; after each reversal there is a visible interval where stored state still has the old sign.

The baseline `30 m/s^2` limit is inactive and bias is zero, so the plots isolate dynamic lag. At the final
sample before the first reversal, applied and measured acceleration are about `19.9990` and `19.9980
m/s^2`; these values follow the independent constant-step equations, not a plotted-curve guess.

## Two isolated levers

- Increasing sensor `tau_s` changes measurement lag and sensor RMS error but cannot change the upstream
  command or actual actuator history. If actual motion changes during this sweep, the implementation has
  coupled the wrong states.
- Increasing actuator `tau_a` changes request-to-applied error and downstream measurement. It cannot change
  the request itself. A sensor cannot report motion the actuator never produced.

Magnitude limit and bias are different mechanisms. Saturation clips the actuator input before dynamics;
bias adds a static offset after sensor dynamics. Calling every mismatch “lag” hides those distinctions.

## Broken bandwidth-separation case

The baseline allows many actuator and sensor time constants within one command plateau. The broken case
reverses the request every `0.1 s` while `tau_a=0.8 s` and `tau_s=0.6 s`. The request changes faster than
either device can settle: actual peak collapses below `3 m/s^2`, measured peak remains below `1 m/s^2`,
and the sensor can report the previous sign after the command reverses.

This is not numerical instability—the exact recurrence remains finite and bounded. It is a recognizable
bandwidth mismatch caused by an input time scale that violates the assumed separation from device dynamics.

## Misconceptions to correct directly

- Requested, limited, applied, sensed, and reported acceleration are different signals.
- A sensor time constant cannot change actual actuator motion in this feed-forward cascade.
- A larger time constant means slower response, not a larger final value for a constant bounded input.
- Saturation is a magnitude constraint; lag is stored dynamic state; bias is a static reporting offset.
- A stale signal can have the wrong sign even when every equation is stable and correctly implemented.
- Exact zero-order-hold arithmetic is still a model, not identified hardware dynamics.
- Static and independent Python simulation evidence do not prove MATLAB execution or rendered UI behavior.
- No bench, HIL, field, calibration, timing, fault-tolerance, or production evidence was produced.

Ask one observation question at a time. Request the teach-back only after executable checks pass.
