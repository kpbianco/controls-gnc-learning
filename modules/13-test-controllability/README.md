# P13 — Test Controllability

**Track:** Controls, State Estimation, Guidance, and Navigation  
**Phase 4:** State-space control  
**Status:** implemented

## Guiding question

What inputs, observable effects, and failure modes matter when you test Controllability?

## Physical mental model

P12 made the gap between requested and available actuator effort visible. P13 asks an earlier design
question in state space: can that actuator move every state direction that matters?

The concrete system has normalized position and rate states. A command accelerates rate, and an
intact kinematic coupling carries rate into position:

```text
d(position)/dt = coupling * rate
d(rate)/dt     = -damping * rate + input_gain * command
```

The traditional two-state test forms `C = [B, A*B]`. The columns show the immediate input direction
and the direction created after the dynamics act once. P13 also builds every exact held-input
reachability column over a finite maneuver, so the learner sees the state motion and the required
command rather than receiving only a rank verdict.

The state coordinates use fixed scales of `1 m` and `1 m/s`. Singular values are therefore useful
comparisons inside this lesson, but they are coordinate-scaled scores, not universal physical
constants. Full rank means a target is mathematically reachable in the model; it does not promise
that a P11/P12 actuator can supply the required peak command.

## Learning flow

1. Read the two state equations and predict whether a rate actuator can eventually move position.
2. Visualize the deterministic baseline state transfer, probe response, and reachability metrics.
3. Move only actuator effectiveness and observe reachability score and command energy.
4. Reset effectiveness, move only maneuver time, and observe how more input opportunities reduce effort.
5. Explain both changes from the visible reachability columns.
6. Disconnect rate from position and recognize the frozen-position, rank-loss symptom.
7. Run deterministic checks and give a two-sentence teach-back.

## Run

From MATLAB with the repository as the current folder:

```matlab
launch_lesson("P13")
interactive
run_module_checks("P13")
```

The implementation uses deterministic base MATLAB arithmetic and no Control System Toolbox
controllability, state-space, simulation, or pseudoinverse helpers. An unreachable target is marked
infeasible with effort reported as N/A; the zero command shown for its failed transfer is not called
an optimum. Retained repository validation
is static plus independent Python reference simulation; no MATLAB-runtime, UI, MATLAB numerical-
fidelity, bench, HIL, field, or production validation is implied.
