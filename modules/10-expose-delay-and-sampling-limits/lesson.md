# P10 lesson: Expose Delay and Sampling Limits

## Guiding question

What inputs, observable effects, and failure modes matter when you expose Delay and Sampling Limits?

## Compounds on

P05 established proportional feedback and its nonzero steady-state error. P07 tied
visible motion to stability reserve. P09 separated sample instants from continuous
plant motion and exposed a held digital command. P10 preserves those ideas and adds
the time required to turn a sampled measurement into an applied command.

## Mental model

The plant is `y' = -y + u`. At each sample the controller computes
`u[k] = 8*(1-y[k])`. Computation takes `Td` seconds, so the actuator cannot apply that
new command immediately. It retains `u[k-1]` during `Td`, then applies `u[k]` for the
remaining `Ts-Td`. The plant never waits for the processor.

The exact interval equation has three contributions:

`y[k+1] = exp(-Ts)*y[k] + wOld*u[k-1] + wNew*u[k]`.

`wOld = exp(-(Ts-Td))*(1-exp(-Td))` measures the stale-command portion, and
`wNew = 1-exp(-(Ts-Td))` measures the new-command portion. Their sum with
`exp(-Ts)` is one. At `Td=0`, `wOld=0`; the new command owns the entire interval.
At `Td=Ts`, `wNew=0`; the whole interval uses the previous command.

The sample-period sweep sets `Td=0` and moves only `Ts`, making the held-update limit
visible. The delay sweep fixes `Ts=0.1 s` and moves only `Td`, making stale-command
time visible. Pole magnitude reports whether deviations shrink (`<1`), persist at
the boundary (`=1`), or grow (`>1`).

The deliberately broken case uses `Ts=0.2 s` and `Td=0.18 s`. Its sample rate still
exceeds twice the continuous closed-loop bandwidth in hertz, but its pole magnitude
exceeds one. That is not a contradiction: Nyquist is a signal-reconstruction bound,
not a complete feedback-stability guarantee. Delay consumes phase and lets old
commands act after the measured error has changed. Reducing only `Td` to `0.02 s`
moves the poles inside the unit circle again.

## Tutor sequence

Ask one prediction before the baseline: which trace exposes latency first? Show the
output comparison, then reveal computed versus applied commands. Move `Ts` once with
zero delay and connect the changed target gap to hold duration. Reset to `Ts=0.1 s`,
move only `Td`, and connect overshoot to stale-command weight. Finally reveal the
broken pole magnitude and Nyquist ratio before the growing output, then recover by
reducing delay without changing sample period.

## Direct misconception corrections

- “The plant pauses while the controller computes.” No. It keeps evolving under
  the previous actuator command.
- “Sample period and computation delay are the same thing.” No. `Ts` spaces
  measurements; `Td` decides how long the prior command persists after each sample.
- “Sampling above Nyquist guarantees stable feedback.” No. Nyquist addresses signal
  reconstruction; feedback also depends on dynamics, gain, hold, and latency.
- “A delayed plot can be repaired by interpolation.” No. Smoothing does not change
  the stale command physically applied during `Td`.
- “The plot proves runtime or hardware behavior.” No. This is retained model content;
  MATLAB runtime, UI, numerical fidelity, bench, HIL, and field validation require
  separate evidence.

## Teach-back

In two sentences, distinguish `Ts` from `Td`, name one observable caused by each,
and explain why the broken case can fail despite its Nyquist ratio plus how it recovers.
