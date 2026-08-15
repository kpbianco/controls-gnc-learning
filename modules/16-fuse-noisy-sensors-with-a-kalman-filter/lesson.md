# P16 lesson: Fuse Noisy Sensors with a Kalman Filter

## Guiding question

What inputs, observable effects, and failure modes matter when you fuse Noisy Sensors with a Kalman Filter?

## Compounds on

P15 — Build a State Observer. P15 introduced model prediction, known input, innovation, correction,
and the danger of trusting a biased measurement. P16 keeps that observer loop and replaces its fixed
gain with covariance-weighted fusion of two noisy position sensors. P15's observability remains
necessary: position changes over time are what reveal rate.

## Mental model

Carry two things through time: the best state estimate and an uncertainty ellipse represented by
`P`. The motion model advances both. Uncertain acceleration adds `Q`, enlarging the predicted
uncertainty. Two position sensors report values and noise variances in `R`. Their innovation
covariance is `S=C*Pminus*C'+R`, and the correction gain is `K=Pminus*C'/S`.

A smaller sensor variance gives that sensor more leverage, but only relative to the other sensor and
the model. A larger process variance says that unmodeled acceleration may have changed the state, so
the filter reports more rate uncertainty and uses later measurements more strongly. Covariance is a
declared model of uncertainty; it is not proof that a sensor obeys the declaration.

Normalized innovation squared (NIS) compares a two-sensor innovation with `S`:

```text
NIS = innovation' * S^(-1) * innovation
```

Because both measurements are positions, each innovation has metres, `S` has square metres, and NIS
is dimensionless. Position and rate covariance metrics stay separate because their units differ.

## What the two levers mean

- **Assumed sensor A noise standard deviation** changes only one diagonal entry of `R`. Raising it
  lowers sensor A's position gain, shifts relative trust toward sensor B and prediction, and makes a
  fixed raw innovation less surprising.
- **Assumed process acceleration standard deviation** changes only `Q`. Raising it increases
  predicted uncertainty, the rate correction gain from position, and reported rate uncertainty.

Every sweep resets seed, actual pseudo-noise, command, outlier, other covariance assumption,
duration, and sample interval. The seeded physical trajectory is therefore identical across each
controlled comparison.

## Deliberately broken assumption

The broken case adds one `+4 m` sample to sensor A at `12 s`. `R` still describes ordinary zero-mean
noise with `0.35 m` standard deviation, so the outlier is much larger than the innovation covariance
predicts. NIS spikes and the gain still moves the estimate: an ordinary Kalman update does not
automatically reject an outlier. A fresh zero-outlier call exactly recovers the baseline because the
model has no global random or persisted state.

## Misconceptions to correct directly

- A Kalman gain is not a magic constant; it follows the current predicted covariance and `R`.
- A smaller `R` does not make the physical sensor quieter. It tells the filter to trust that sensor.
- A larger `Q` does not add noise to the already seeded truth in a sweep. It changes what the filter
  assumes about model error.
- Two sensors do not guarantee correctness when their uncertainty or mean is modeled incorrectly.
- NIS is a consistency diagnostic, not automatic outlier rejection and not proof of Gaussian data.
- Seeded pseudo-noise and independent reference simulation are not MATLAB-runtime or sensor evidence.

Ask one observation question at a time, then request the teach-back only after executable checks.
