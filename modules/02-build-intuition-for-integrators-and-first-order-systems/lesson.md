# Lesson: Build Intuition for Integrators and First-Order Systems

## Guiding question

What inputs, observable effects, and failure modes matter when you build Intuition for Integrators and First-Order Systems?

## Compounds on P01

P01 showed a physical state changing because energy was stored and dissipated. Here
we strip that system down to two elemental behaviors. An integrator is pure storage;
a first-order system stores one state while continuously closing its gap to an
equilibrium. These blocks will reappear inside plants, actuators, sensors, observers,
and controllers later in the track.

## Mental model

For a normalized input `u`, an ideal integrator obeys

```text
dx_I/dt = u.
```

The output is accumulated area. A constant positive input therefore produces a
constant positive slope, not a finite settling value.

A first-order system obeys

```text
tau * dy/dt + y = K * u,
```

or `dy/dt = (K*u - y)/tau`. The rate is proportional to the remaining gap. Under a
step of amplitude `A`, the response is `K*A*(1-exp(-t/tau))`; after one `tau` it has
closed about 63.2% of the gap, and after four `tau` it is close to settled.

## Observe before manipulating

Run the baseline section of `experiment.m`. Ask only this prediction first: which
output can settle while the positive input remains applied? In the output view,
observe the ramp beside the bounded exponential. Then inspect the rate view: the
integrator rate stays constant while the first-order rate decays toward zero.

## Move one lever at a time

First change only input amplitude. The integrator slope and first-order equilibrium
scale with amplitude. Reset the amplitude, then change only `tau`. The first-order
curve stretches or compresses in time, but its equilibrium `K*A` does not change.
Use `interactive.m` to repeat those isolated moves.

## Deliberately broken assumption

The continuous first-order system is stable for positive `tau`, but an explicit-Euler
calculation is only stable here when `0 < dt/tau < 2`. The broken case uses
`dt/tau = 3`; its sampled error alternates and grows even though the exact response
settles. The violated assumption is that the numerical interval resolves the system
dynamics. The symptom is invented oscillatory divergence, not physical instability.

## Common misconceptions

- An integrator is not merely a very slow first-order system: the integrator has no
  finite DC equilibrium under a nonzero constant input.
- `tau` changes response speed, not the first-order equilibrium.
- Reaching 63.2% after one time constant does not mean 63.2% is the final value.
- A plausible numerical plot is not automatically a faithful model of the governing
  equation.

## Completion standard

Pass `run_checks.m`, answer the interpretation questions in `checks.md`, and give a
two-sentence teach-back that connects the visible behavior to both equations without
using MATLAB syntax as the explanation.
