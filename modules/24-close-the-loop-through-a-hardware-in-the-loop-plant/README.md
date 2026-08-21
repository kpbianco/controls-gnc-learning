# P24 — Close the Loop Through a Hardware-in-the-Loop Plant

**Track:** Controls, State Estimation, Guidance, and Navigation

**Phase 6:** Guidance and HIL

**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you close the Loop Through a Hardware-in-the-Loop Plant?

## Physical and computational mental model

P23 separated a request from actuator motion and sensor reporting. P24 closes feedback across the next
boundary: the controller receives a timestamped plant measurement, computes a bounded force, and sends a
timestamped command to a plant-side receiver. The plant keeps evolving while packets travel.

```text
virtual plant --measurement(timestamp)--> controller
virtual plant <--command(force)---------- controller
                                     |
                          command-age watchdog
                                     |
                             zero-force fallback
```

The plant is a transparent one-dimensional mass–damper system:

```text
x_dot = v                                      [m/s]
m*v_dot = u_applied - c*v                      [N]
u_request = clip(18*(r-x_measured)-8*v_measured, -30, 30)  [N]
```

Its fixed-step update is the exact constant-force solution, not an ODE, transfer-function, Simulink, or
networking black box. Virtual packet queues use integer ticks. Cancellation is evaluated before same-tick
delivery; it purges queued commands and applies zero. If the age of the last delivered command reaches the
watchdog timeout, the receiver also applies zero.

This is a **HIL-shaped software emulator** for learning interface contracts. It performs no wall-clock
scheduling, socket or bus I/O, target synchronization, hardware actuation, or physical HIL validation.

## Deterministic baseline and two levers

The baseline uses a `0.05 s` controller period, `0.01 s` one-way latency, `0.2 s` watchdog timeout, no
drops, no cancellation, `1.5 kg` mass, `0.01 s` plant tick, and `8 s` virtual duration. The reference is
`+1 m` for four seconds, then `-0.5 m` for four seconds.

- One-way-latency sweep `[0.01 0.02 0.04 0.06 0.08] s`: only delivery ticks move. Measurement age rises
  before the changed command timing alters tracking and peak position.
- Controller-period sweep `[0.02 0.04 0.05 0.1 0.2] s`: the transport, watchdog, plant, and solver tick
  reset. A longer period sends fewer commands and holds older feedback; the coarsest release visibly loses
  closed-loop quality.
- Plant mass, deterministic command-drop cadence, watchdog timeout, and a `4.01 s` simulated cancellation are
  available in the UI only after the two timing levers are understood.

## Deliberately broken case, rollback, and recovery

The broken case runs the controller every `0.1 s`, uses `0.04 s` one-way latency and a `0.12 s` watchdog,
then drops every second command. The command stream now has `0.2 s` gaps: the receiver's age limit expires,
so safe zero repeatedly replaces the stale held force. Removing only the drop cadence restores continuous
delivery for the same controller, transport, watchdog, plant, and grid.

A separate cancellation case cancels at exactly `4.01 s`, when the command sourced at `4 s` is due. It proves cancellation wins a delivery tie, purges
pending work, and keeps all later applied force at zero. A fresh baseline call exactly recovers because the
model has no global, persistent, random, file, network, timer, or asynchronous state.

## Run it

From the repository root, use `launch_lesson("P24")`. To open only the UI while preventing another
module's generic `model` function from winning path resolution:

```matlab
moduleFolder = fullfile(pwd,"modules","24-close-the-loop-through-a-hardware-in-the-loop-plant");
addpath(moduleFolder,"-begin");
clear model interactive;
try
    interactive;
catch exception
    rmpath(moduleFolder);
    rethrow(exception);
end
rmpath(moduleFolder);
```

Run checks with `run_module_checks("P24")`.

## Dependencies and evidence boundary

The module uses base MATLAB arithmetic, plotting, and `uifigure` controls only. Retained source checks and
an independent Python oracle can establish static and simulated facts about the declared virtual model.
No MATLAB-runtime, rendered-UI, MATLAB numerical-fidelity, wall-clock timing, external protocol, bench,
physical HIL, field, RT1/RT2, Unreal, signing, deployment, staging, release, or production evidence is
implied without separate retained results from the required named environment.
