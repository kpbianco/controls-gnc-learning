# Lesson: Relate Poles to Visible Motion

## Guiding question

What inputs, observable effects, and failure modes matter when you relate Poles to Visible Motion?

## Compounds on P02

P02 showed a first-order response settling with the exponential factor
`exp(-t/tau)`. Its pole is `-1/tau`: moving that real pole left makes the
exponential vanish faster. P03 extends the same idea to a conjugate pair. The real
coordinate still controls an exponential, while an imaginary coordinate makes the
state alternate direction.

## Mental model

For poles `p = sigma +/- j*omega`, free displacement follows

```text
x'' - 2*sigma*x' + (sigma^2 + omega^2)*x = 0
x(t) = exp(sigma*t) * (x0*cos(omega*t) + B*sin(omega*t))
B = (v0 - sigma*x0)/omega.
```

The inputs are the two pole coordinates, initial displacement `x0` in metres,
initial velocity `v0` in metres per second, and the observation grid. The primary
observables are displacement, its exponential envelope, the pole-plane location,
cycle period, and unit-mass mechanical energy.

- `sigma < 0` means left-half-plane poles and a shrinking envelope.
- `sigma = 0` means imaginary-axis poles and sustained motion.
- `sigma > 0` means right-half-plane poles and a growing envelope.
- `omega > 0` gives period `T = 2*pi/omega`; larger `omega` packs cycles closer.
- `omega = 0` is a repeated real pole, handled by its exact nonoscillatory limit.

Initial conditions decide phase and visible amplitude, but they do not move the
poles. Likewise, a pole pair predicts the mode's shape in time; it does not specify
how strongly an external input excites that mode.

## Observe before manipulating

Run only the baseline sections of `experiment.m`. Make one prediction first: will
the released displacement reverse direction, and will its envelope grow or shrink?
Observe the motion view, then locate the same `sigma` and `omega` on the pole plane.

## Move one lever at a time

First sweep only `sigma`. More-negative values shrink the envelope faster while
`omega = 2 rad/s` preserves the `pi`-second cycle spacing. Reset `sigma`, then sweep
only `omega`. The period changes in inverse proportion, while the common real part
preserves `exp(-0.5*t)` as the envelope ratio. The natural frequency changes when
either coordinate moves, so call the controls pole coordinates rather than treating
the real-part control as an isolated physical damper.

## Deliberately broken assumption and recovery

The broken case violates the assumption that the mode dissipates energy and its
poles remain in the left half-plane. Moving `sigma` from `-0.25` to `+0.25 1/s`
crosses the stability boundary. The cycle spacing stays fixed because `omega` did
not move, but the envelope and unit-mass energy grow outward. Restoring the negative
real coordinate recovers decay without changing the imaginary coordinates.

## Common misconceptions

- Pole plots are not abstract decorations: horizontal position maps to envelope
  growth or decay, and vertical distance maps to cycle spacing.
- A negative real part does not mean the displacement is always negative; it means
  the exponential envelope decays.
- A larger imaginary part means faster oscillation, not faster envelope decay.
- Initial displacement and velocity change the visible phase and scale, not the pole
  locations.
- A sampled curve that looks bounded for a short window is not proof of stability;
  the pole real part and longer-horizon envelope reveal growth.

## Completion standard

Pass `run_checks.m`, answer the interpretation questions in `checks.md`, and give a
two-sentence teach-back: mechanism first, visible consequence second. MATLAB syntax
is not an explanation.
