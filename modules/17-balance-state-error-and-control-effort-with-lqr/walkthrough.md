# P17 walkthrough: Balance State Error and Control Effort with LQR

## Read and predict

Read the guiding question and cost in `README.md`. Make one prediction: with control price fixed,
does raising the position-error weight increase or decrease the first acceleration command?

## Baseline

Run the baseline sections of `experiment.m`.

1. The cart starts with `1 m` position error and zero rate error.
2. Negative acceleration first creates rate toward the origin; position and rate then decay.
3. Commanded and applied acceleration coincide because the baseline actuator has full authority.
4. The feedback gain, pole radius, settling time, position integral squared error, effort integral,
   and peak acceleration make both sides of the tradeoff visible.
5. Repeating the same call returns exactly the same matrices, trajectory, and metrics.

Mechanism: P16 supplied the state estimate. P17 uses `Q`, `R`, the nominal `A,B` model, and future
cost `P` to form `u=-K*x`.

## Lever 1 — position-error weight

Keep `r=1`, actuator effectiveness `1`, initial position `1 m`, duration `12 s`, and interval
`0.02 s`. Sweep `q_p` through `[0, 0.25, 1, 4, 16]`.

- Position gain and squared-command effort integral rise as displacement becomes more expensive.
- Position integral squared error falls.
- At `q_p=0`, position gain and commanded acceleration are exactly zero for this stationary offset;
  the error persists because the objective does not charge it.

Read the `Q → P → K` mechanism only after observing the changed view.

## Lever 2 — control-effort weight

Reset `q_p=4`, then sweep `r` through `[0.1, 0.25, 1, 4, 10]`.

- Higher `R+B'*P*B` produces smaller feedback gains and peak command.
- The effort integral falls while settling takes longer.
- The plant, state, and state prices are identical across the sweep.

## Broken case and recovery

Select `Disconnected actuator (broken)`.

1. The gain is unchanged because it was designed for the nominal `B`.
2. The controller repeatedly commands acceleration from the persistent state error.
3. Applied acceleration is zero, so position remains at `1 m` and settling is not achieved.
4. Restore full authority; a fresh call exactly matches the baseline.

## Check and teach back

Run `run_module_checks("P17")`. Answer the interpretation questions in `checks.md`, then give the
two-sentence teach-back. Learner completion remains separate from batch implementation.
