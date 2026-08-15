# P17 lesson: Balance State Error and Control Effort with LQR

## Guiding question

What inputs, observable effects, and failure modes matter when you balance State Error and Control Effort with LQR?

## Compounds on

P16 — Fuse Noisy Sensors with a Kalman Filter. P16 made full-state feedback feasible by producing a
position/rate estimate and covariance. P17 uses the exact state in its deterministic model to isolate
the control-design tradeoff. In practice LQR acts on P16's estimate, not inaccessible truth. P13's
controllability lesson also returns: an actuator must influence every state the design must regulate.

## Mental model

Imagine assigning prices before driving the cart back to the origin. `Q` charges for state error and
`R` charges for the command. A high position price makes lingering displacement costly. A high input
price makes a hard acceleration costly. LQR finds one feedback gain that minimizes their declared
sum for the nominal linear plant; it does not minimize each term separately.

The Riccati matrix `P` is a map from the current state to future cost. At convergence, one additional
Bellman step does not change it:

```text
P = Q + A'*P*A - A'*P*B*(R + B'*P*B)^(-1)*B'*P*A
```

The model computes that scalar division and matrix recurrence directly. The closed-loop poles of
`A-B*K` must lie inside the unit circle for nominal sampled regulation.

## What the two levers mean

- **Position-error weight `q_p`** changes only the position entry of `Q`. Raising it increases the
  position feedback gain, reduces position integral squared error, and increases the squared-command
  effort integral.
  At exactly zero, a stationary position offset costs nothing; position gain is zero and the offset
  persists. That is an interpretable limiting case, not a numerical crash.
- **Control-effort weight `r`** changes only scalar `R`. Raising it makes input more expensive, lowers
  feedback gains and peak acceleration, reduces the effort integral, and generally lengthens settling.

Every sweep resets actuator effectiveness, initial state, duration, interval, and the non-swept
weight. The comparisons therefore isolate the declared lever.

## Deliberately broken assumption

The controller is designed with the nominal input column `B`, which represents full acceleration
authority. The broken case sets actual actuator effectiveness to zero after design. Commanded
acceleration remains nonzero, applied acceleration is exactly zero, and the position error cannot
change. LQR optimality is conditional on the model and cannot restore a disconnected actuator or
lost controllability. A fresh effectiveness-one call exactly recovers the baseline.

## Misconceptions to correct directly

- LQR is not automatically “aggressive”; behavior follows the relative state and input prices.
- An effort price discourages large input but does not enforce a hard actuator limit.
- Larger `Q` does not change the physical initial error. It changes how expensive that error is.
- Larger `R` does not weaken the actuator. It asks the design to use the actuator more sparingly.
- A small weighted cost is meaningful only with declared state/input scales and weights.
- Stable nominal poles do not prove performance when actuator authority or the plant model is wrong.
- The guarantee is for an unconstrained nominal linear model, available state, quadratic cost, and
  correct actuator authority; it is not a general robustness guarantee.
- Independent reference simulation is not MATLAB-runtime, UI, hardware, or field evidence.

Ask one observation question at a time and request the teach-back only after executable checks.
