# P20 lesson: Compare Nominal and Robust Designs

## Guiding question

What inputs, observable effects, and failure modes matter when you compare Nominal and Robust Designs?

## Compounds on P19

P19 held one controller fixed while actuator effectiveness and drag changed. P20 keeps that
transparent uncertain speed plant, then compares one controller tuned for the matched model with a
second controller selected against the declared 25-point positive uncertainty grid.

## Mental model

A nominal design is like choosing cruise-control gains on a calm, level road. A robust design asks
which candidate has the smallest worst tracking-error integral over the roads that were explicitly
put on the test map, while rejecting candidates that exceed the declared command-effort budget.
The answer can be more conservative at the exact center and still be preferable at the difficult
edge. Neither label replaces the need to state the map, objective, constraint, and failure boundary.

The plant still obeys P19's exact held-input recurrence:

```text
alpha = exp(-a*dt),  beta = (b/a)*(1-alpha)
v[k+1] = alpha*v[k] + beta*u[k]
```

The nominal controller uses a model-matched feedforward command plus proportional feedback. The
robust controller uses proportional-integral feedback. Its integral state accumulates tracking
error in metres, so `Kp` has units `1/s`, `Ki` has units `1/s^2`, and both command terms have units
`m/s^2`.

## What the comparison reveals

- At the matched plant, the nominal controller has the smaller tracking ISE and reaches the target
  faster. That is its intended operating point.
- On the 25 declared actuator/drag points, the selected PI candidate has a smaller worst-case
  12-second ISE while every grid scenario remains stable and below the effort limit for the `1 m/s`
  design step at `dt=0.02 s`. Other reference amplitudes are exploratory, not effort guarantees.
- Integral action makes the robust controller's stable positive-plant equilibrium error exactly
  zero, but a finite 12-second run can still end before a slow worst-corner transient settles.
- The robust design can use more effort at the worst corner. Robustness is a trade, not dominance on
  every metric or every plant.

## Deliberately broken assumption

The finite design search includes only positive actuator effectiveness. Reverse actuator polarity
and positive error drives speed in the wrong direction. Both controllers then have a discrete pole
magnitude above one and the bounded simulator terminates a diverging trace before it can consume an
unbounded numerical range. Restoring positive polarity in a fresh call recovers the exact baseline;
no controller state leaks between runs.

## Misconceptions to correct directly

- “Robust” does not mean best at the nominal point.
- A finite uncertainty grid is not proof for values between grid points or outside its limits.
- Zero asymptotic PI error is not the same as zero error at the finite experiment horizon.
- Lower worst-case tracking error does not mean lower command effort.
- Reversed polarity is a structural failure, not a larger positive gain error.
- Explicit enumeration is a transparent comparison, not a toolbox synthesis or universal optimum.
- Independent reference simulation is not MATLAB-runtime, UI, bench, HIL, or field evidence.

Ask one observation question at a time. Request the teach-back only after executable checks pass.
