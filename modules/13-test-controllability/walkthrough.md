# P13 walkthrough: Test Controllability

## Read and predict

Read the guiding question and the two state equations in `README.md`. Make one prediction: can a
command that enters only the rate equation eventually move position when coupling is intact?

## Baseline

Run the baseline sections of `experiment.m`.

1. The minimum-energy command first builds positive rate, then reverses to finish at `1 m` with
   zero rate after `2 s`.
2. A fixed positive probe changes rate immediately; position accumulates afterward through the
   coupling.
3. The two traditional controllability columns and the finite-horizon Gramian both have rank two.
4. The terminal residual is numerical roundoff, while peak command and command-energy remain
   separate feasibility warnings.

Mechanism: every reachability column is one held command's terminal-state effect. The dynamics make
earlier rate changes contribute to position, so the columns span two state directions.

## Lever 1 — actuator effectiveness

Keep coupling at `1`, maneuver time at `2 s`, interval at `0.05 s`, and target at `1 m`.

- Smaller effectiveness shortens every reachability column.
- Rank stays two for the nonzero sweep values.
- The weakest singular value grows with effectiveness, while required energy falls with its square.

Read the explanation only after comparing score and effort.

## Lever 2 — maneuver time

Reset effectiveness to `1 (m/s^2)/command` and sweep `0.5–4 s`.

- Short transfers require large positive and negative commands.
- Longer transfers add useful input opportunities and reduce energy and peak command.
- `A`, `B`, damping, target, and interval stay fixed; only the horizon changes.

## Broken case and recovery

Set coupling to zero while retaining the same actuator and probe.

1. Broken-case rate matches the intact probe response.
2. Broken-case position remains exactly zero.
3. Rank is one and the requested position target retains a `1 m` residual.
4. Restore coupling to one; position responds, rank returns to two, and the target is reconstructed.

## Check and teach back

Run `run_module_checks("P13")`. Answer the interpretation questions in `checks.md`, then give the
two-sentence teach-back. Learner completion remains separate from batch implementation.
