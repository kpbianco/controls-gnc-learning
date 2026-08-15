# P14 walkthrough: Test Observability

## Read and predict

Read the guiding question and the state/measurement equations in `README.md`. Make one prediction:
can a position sensor reveal initial rate even though rate is not measured directly?

## Baseline

Run the baseline sections of `experiment.m`.

1. The true state starts at `0.8 m` and `0.6 m/s`; the comparison state has the same rate but a
   position offset of `1 m`.
2. Both rates decay identically, and the two positions remain one metre apart.
3. Position measurement separates the candidates at every sample.
4. The initial-rate observation column begins at zero and grows as rate accumulates into position.
5. The traditional observability rows and finite-window Gramian both have rank two, and the
   noise-free initial-state reconstruction error is numerical roundoff.

Mechanism: every observation row is one sample's view of the initial state. Dynamics carry initial
rate into later position, so the stacked rows span two state directions.

## Lever 1 — position-sensor sensitivity

Keep position measurement selected, window at `2 s`, interval at `0.05 s`, and both candidate states
fixed.

- Smaller sensitivity shrinks every observation row and the candidate-output separation.
- Rank stays two for the nonzero sweep values.
- The weakest singular value grows with sensitivity, while worst-case inverse noise gain falls.

Read the explanation only after comparing separation and inverse gain.

## Lever 2 — observation-window duration

Reset sensitivity to `1 sensor unit/m` and sweep `0.1–4 s`.

- A short history contains little accumulated evidence about initial rate.
- A longer history adds rows and strengthens the weakest observation direction.
- Damping, initial states, sample interval, and sensor stay fixed; only the window changes.

## Broken case and recovery

Select rate-only measurement while retaining the same gain and candidate states.

1. The sensor produces a healthy decaying rate signal.
2. The two different initial positions produce exactly the same output history.
3. Rank is one and the full initial state is non-unique.
4. Restore position measurement; output separation returns, rank returns to two, and the initial
   state is reconstructed.

## Check and teach back

Run `run_module_checks("P14")`. Answer the interpretation questions in `checks.md`, then give the
two-sentence teach-back. Learner completion remains separate from batch implementation.
