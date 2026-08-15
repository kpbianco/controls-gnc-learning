# P15 lesson: Build a State Observer

## Guiding question

What inputs, observable effects, and failure modes matter when you build a State Observer?

## Compounds on

P14 — Test Observability. P14 showed that position measurement history distinguishes position and
rate for this cart. Full observability is the permission to build an observer, not the observer
itself. P15 adds prediction, innovation, correction gain, and a running initial estimate. P16 will
handle stochastic sensor fusion; this lesson uses only deterministic interference.

## Mental model

Think of two copies of the cart. The physical copy receives a known acceleration command. The
observer copy receives the same command and predicts position and rate. Only physical position is
measured. At each sample, `innovation = measured position - predicted position` tells the observer
how its prediction disagrees with the sensor, and `L*innovation` corrects both state estimates.

For the matched noise-free case, the known input cancels from the estimation error:

```text
error[k+1] = (Ad - L*C) error[k]
```

The lesson requests a repeated error pole `q = exp(-speed*dt)`. Smaller `q` means faster sampled
decay, but the required gain is stronger. Metres and metres per second are normalized by declared
scales of `1 m` and `1 m/s` before their errors are combined into one norm.

## What the two levers mean

- **Observer pole speed** changes the desired decay of initial-estimate error. In the fixed eight-second
  sweep, faster poles leave less final error and require a larger correction gain.
- **Measurement-interference amplitude** changes only a repeatable `2.5 Hz` position disturbance.
  The observer cannot know whether innovation came from true state error or sensor interference, so
  both position and rate estimates acquire ripple.

Each sweep resets the other lever, sensor bias, command, duration, sample interval, true initial
state, and estimated initial state.

## Deliberately broken assumption

The broken case adds a constant `+0.15 m` calibration bias to the position sensor. The measurement
path remains observable and the observer error poles remain stable. Nevertheless, the observer
eventually estimates position about `0.15 m` too high while innovation approaches zero. This is the
recognizable false-confidence symptom: a quiet residual can mean agreement with a biased sensor,
not agreement with truth. Restoring zero bias in a fresh call recovers the deterministic baseline.

## Misconceptions to correct directly

- Observability does not choose `L`, guarantee a useful transient, or reject sensor bias.
- A faster observer is not free: stronger correction also passes more measurement disturbance.
- The observer does not measure rate secretly; rate changes predicted position, then position
  innovation corrects the rate estimate.
- A known input belongs in both plant and observer prediction. It cancels from matched estimation
  error, but it still drives the physical and estimated trajectories.
- Deterministic sinusoidal interference is not stochastic noise validation and is not a Kalman filter.
- A small innovation is evidence of sensor-model agreement, not independent proof of state accuracy.

Ask one observation question at a time, then request the teach-back only after executable checks.
