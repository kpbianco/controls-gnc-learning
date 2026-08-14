# Lesson: Compare Linear and Nonlinear Pendulum Models

## Guiding question

What inputs, observable effects, and failure modes matter when you compare Linear and Nonlinear Pendulum Models?

## Compounds on P03

P03 related a linear second-order equation to a pole pair and visible oscillation.
For a pendulum near its hanging equilibrium, the linearized equation has natural
frequency `wn = sqrt(g/L)` and poles determined by `wn` and damping ratio `zeta`.
P04 keeps that linear prediction beside the physical nonlinear restoring law so the
approximation boundary becomes observable.

## Mental model

For angle `theta` in radians,

```text
nonlinear restoring acceleration = -(g/L)*sin(theta)
linear restoring acceleration    = -(g/L)*theta.
```

The approximation is local, not magical. Around zero, `sin(theta) = theta -
theta^3/6 + ...`, so the omitted term is tiny. At a large angle, the linear term has
too much magnitude. It pulls the prediction toward zero too quickly, shortening the
predicted cycle relative to the nonlinear pendulum.

The inputs are release angle, release angular rate, length, damping ratio, and the
calculation grid. The primary observables are both angle histories, restoring-law
curves, first-zero times, phase error, period scale, and specific mechanical energy.

## Observe before manipulating

Run only the baseline sections of `experiment.m`. Make one prediction: after a
20-degree release, will the nonlinear curve lead or lag the linear curve? Observe
the angle history first, then use the restoring-law plot to explain the direction of
the accumulating phase error.

## Move one lever at a time

First sweep release angle while length stays at `1 m`. The five-degree curves nearly
overlap; the 90-degree curves separate because `sin(theta)` no longer follows
`theta`. Reset to 20 degrees, then sweep only length. Since
`T_small = 2*pi*sqrt(L/g)`, longer pendulums move more slowly. Length changes the
clock for both models; release angle changes the approximation error.

## Deliberately broken assumption and recovery

The broken case trusts the small-angle substitution at 120 degrees. There,
`theta = 2.094 rad` but `sin(theta) = 0.866`, so the linear model begins with more
than twice the restoring magnitude and runs ahead. Recover by reducing the release
to five degrees, or use the nonlinear model when large-angle timing matters.

## Common misconceptions

- “Linear” does not mean the line traced by the pendulum bob; it means the state
  appears only to the first power in the governing equation.
- Degrees are convenient for controls and labels, but `sin(theta) approximately
  theta` requires radians.
- A deterministic numerical curve is not automatically a faithful physical model;
  the approximation and the calculation step are separate assumptions.
- Length changes the natural time scale in both models. It does not make a large
  angle small.
- Model disagreement is not numerical instability here. The broken case is a valid
  calculation with an invalid small-angle interpretation.

## Completion standard

Pass `run_checks.m`, answer the interpretation questions in `checks.md`, and give a
two-sentence teach-back: mechanism first, visible consequence second. MATLAB syntax
is not an explanation.
