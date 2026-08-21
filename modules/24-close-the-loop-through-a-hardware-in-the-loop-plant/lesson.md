# P24 lesson: Close the Loop Through a Hardware-in-the-Loop Plant

## Guiding question

What inputs, observable effects, and failure modes matter when you close the Loop Through a Hardware-in-the-Loop Plant?

## Compounds on P23

P23 showed that requested, limited, applied, sensed, and reported motion are different signals. P24 retains
that boundary and asks what happens when the controller and plant side exchange those values as timestamped
messages. A mathematically correct controller can still act on an old measurement; a correct plant can
still hold an old command; a receiver can deliberately replace stale input with safe zero.

P10 already distinguished sample spacing from computation delay. P24 compounds that idea into two
transport directions, explicit timestamps, loss, watchdog state, cancellation ordering, and a mechanical
plant that never pauses for software.

## Visible equations and event order

The virtual plant is a mass `m` with viscous damping `c=1.2 N*s/m`:

```text
x_dot = v
m*v_dot = u_applied - c*v
u_request = clip(Kp*(r-x_measured) - Kd*v_measured, -u_max, +u_max)
Kp = 18 N/m, Kd = 8 N*s/m, u_max = 30 N
```

For a held force during one plant tick `dt`, `a=exp(-c*dt/m)` and the source evaluates

```text
v_next = a*v + (1-a)*u/c
x_next = x + (m/c)*(1-a)*v + (dt/c - m*(1-a)/c^2)*u
```

At each integer tick the model evaluates cancellation first; a cancellation invalidates queued work before
anything can arrive at that same timestamp. Otherwise the plant enqueues a measurement on a controller
release, delivers any measurement due now, computes from the newest delivered timestamp, enqueues or drops
the command, delivers any command due now, evaluates command age, and then propagates the plant. This order
makes zero latency a genuine same-tick limit and makes the safety precedence testable.

## What the baseline reveals

The position plot answers whether the loop tracks. The protocol view answers why: measurement age shows
how old the controller's information is, controller force shows what software requested, and applied force
shows what crossed the plant-side boundary after latency and watchdog logic.

The controller period `T_c`, one-way latency `L`, watchdog timeout `T_w`, command-drop schedule, cancel time,
plant mass, plant tick, and virtual duration are inputs. Observable effects include timestamp age, packet
counts, tracking error, peak position and velocity, requested versus applied force, and watchdog duration.

## Two isolated levers

- Increasing only `L` moves measurement and command deliveries later. It does not change controller release
  times, plant parameters, or plant integration. Measurement age is the earliest visible effect; tracking
  changes downstream.
- Increasing only `T_c` reduces update count and holds each delivered sample and command longer. It does
  not coarsen the `0.01 s` plant tick, so the changed trajectory is a feedback-release effect rather than a
  plotting or solver-resolution artifact.

Faster is not automatically proof of a good interface, and slower is not automatically unsafe. The point
of each sweep is to isolate which clock moved and then observe its downstream effect.

## Broken command continuity and explicit safe states

Dropping every second command when the controller sends every `0.1 s` creates `0.2 s` delivery gaps. A
`0.12 s` watchdog refuses to hold the last force that long, so it repeatedly substitutes zero. The
recognizable symptom is not just position error: the protocol-state plot shows exactly when a dropped
packet leads to a stale command and safe-zero action. Removing only the drops recovers continuous delivery.

Cancellation is different from timeout. At the declared cancel timestamp it immediately invalidates every
queued command and forces zero, even if a command was due on that same tick. Neither action proves the
plant is physically safe; it proves only the declared software-emulator rule.

## Misconceptions to correct directly

- A plant does not pause while a controller waits for packets.
- Controller period, one-way latency, measurement age, and command age are different quantities.
- A computed command is not an applied command until it crosses the plant-side boundary.
- Packet loss does not itself apply zero; the receiver's age policy decides when to stop holding stale data.
- Watchdog timeout and cancellation have different triggers, but both use a declared zero-force fallback.
- Bounded virtual state does not prove closed-loop stability for untested dynamics or safe physical motion.
- The word HIL in the curriculum title does not turn a software emulator into physical HIL evidence.
- Static and independent simulated evidence do not prove MATLAB execution, UI rendering, real-time timing,
  protocol compatibility, target scheduling, hardware I/O, bench behavior, or field performance.

Ask one observation question at a time. Request the teach-back only after executable checks pass.
