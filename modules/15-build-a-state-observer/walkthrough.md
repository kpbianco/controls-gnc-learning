# P15 walkthrough: Build a State Observer

## Read and predict

Read the guiding question and the prediction/correction equation in `README.md`. Make one prediction:
can position innovation correct the wrong rate estimate even though rate is never measured directly?

## Baseline

Run the baseline sections of `experiment.m`.

1. The true cart starts at `0.8 m` and `-0.3 m/s`; the observer starts at `-0.4 m` and `0.4 m/s`.
2. A known `0.4 m/s^2` acceleration begins at `0.5 s` and enters both predictions.
3. Position innovation initially is large because the estimated position is wrong.
4. The position estimate converges toward measured position, and the unmeasured rate estimate also
   converges because rate error changes later position predictions.
5. With no interference or bias, the normalized error follows the visible `Ad-L*C` recurrence.

Mechanism: P14 supplied an observable measurement path. P15 feeds its disagreement back through a
designed gain so the estimation error has stable sampled dynamics.

## Lever 1 — observer pole speed

Keep interference and bias at zero, command at `0.4 m/s^2`, duration at `8 s`, and interval at
`0.02 s`. Sweep `1–4 1/s`.

- The requested repeated pole moves farther inside the unit circle as speed increases.
- Fixed-horizon final error decreases for these controlled runs.
- The observer-gain norm increases, showing that faster correction demands more innovation feedback.

Read the mechanism only after comparing the pole, final error, and gain views.

## Lever 2 — deterministic measurement interference

Reset observer speed to `2 1/s`, then sweep interference amplitude from `0–0.05 m`.

- True state and command remain identical in every run.
- Last-second position- and rate-error ripple grow with sensor disturbance.
- Rate ripple appears even though only position is disturbed because `L` corrects both estimates.

## Broken case and recovery

Add a constant `+0.15 m` position-sensor bias.

1. The observer remains numerically stable.
2. Innovation becomes nearly zero.
3. Estimated position remains about `0.15 m` too high, so true-minus-estimated position approaches
   `-0.15 m`.
4. Restore zero bias; the original baseline returns in a fresh isolated run.

## Check and teach back

Run `run_module_checks("P15")`. Answer the interpretation questions in `checks.md`, then give the
two-sentence teach-back. Learner completion remains separate from batch implementation.
