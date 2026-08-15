# P16 walkthrough: Fuse Noisy Sensors with a Kalman Filter

## Read and predict

Read the guiding question and covariance equations in `README.md`. Make one prediction: with both
sensors measuring position, which one should receive more position gain when sensor A reports
`0.35 m` noise and sensor B reports `0.8 m`?

## Baseline

Run the baseline sections of `experiment.m`.

1. Both raw sensor traces scatter around the same true position.
2. The fused position is smoother than either raw sequence because prediction and both measurements
   share the correction.
3. Rate is reconstructed from position history and the P15 motion model; no rate sensor is hidden.
4. Posterior rate standard deviation and NIS make the filter's uncertainty claim visible.
5. The fixed seed makes truth, measurements, estimates, gains, and metrics repeat exactly.

Mechanism: P15 supplied prediction and innovation feedback. P16 propagates `P`, adds `Q`, combines
prediction and sensor variance in `S`, and calculates a new covariance-weighted gain.

## Lever 1 — reported sensor A noise

Keep assumed process acceleration noise at `0.08 m/s^2`, sensor B at `0.8 m`, outlier at zero, seed
at `1601`, duration at `20 s`, and interval at `0.05 s`. Sweep sensor A from `0.1–0.9 m`.

- Sensor A's steady position gain falls as its reported noise grows.
- Sensor B's relative contribution grows because its own noise declaration is unchanged.
- Under-reporting the actual `0.35 m` noise makes mean NIS too large for the claimed covariance.

Read the `R → S → K` mechanism only after comparing the gain and NIS view.

## Lever 2 — assumed process acceleration noise

Reset sensor A to `0.35 m`, then sweep process noise from `0.01–0.5 m/s^2`.

- Larger `Q` makes the prediction admit more unmodeled acceleration.
- Rate gain from position innovation increases.
- Reported posterior rate standard deviation increases.
- Truth and both raw sensor sequences remain identical because the seed and actual process noise do
  not change.

## Broken case and recovery

Inject one `+4 m` outlier into sensor A at `12 s`.

1. The true state, ordinary pseudo-noise, commands, gains, and covariance remain unchanged.
2. Sensor A's innovation leaves the range predicted by `S`.
3. NIS spikes and the fused estimate receives an unsupported correction that may help or hurt by chance.
4. Restore zero outlier; a fresh call returns the exact baseline.

## Check and teach back

Run `run_module_checks("P16")`. Answer the interpretation questions in `checks.md`, then give the
two-sentence teach-back. Learner completion remains separate from batch implementation.
