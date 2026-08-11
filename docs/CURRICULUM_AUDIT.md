# Curriculum readiness audit

**Track:** Controls, State Estimation, Guidance, and Navigation

## Baseline conclusion

The repository has 24 uniquely identified modules in a six-phase, prerequisite-ordered sequence. P01 is the complete reference slice; P02-P24 are explicit non-runnable batch scaffolds. The learner flow is read → visualize → move one lever → visualize the delta → read/explain, followed by a broken case, checks, and teach-back.

Static structure and CLI behavior are verified in CI. MATLAB was not available during the 2026-08-11 baseline audit, so numerical execution, UI behavior, and instructional efficacy remain named validation gaps rather than implied evidence.

## Coverage and compounding order

### Phase 1: Dynamic systems

- **P01 — Watch a Mass-Spring-Damper Respond:** How do mass, stiffness, and damping determine visible motion?
- **P02 — Build Intuition for Integrators and First-Order Systems:** What inputs, observable effects, and failure modes matter when you build Intuition for Integrators and First-Order Systems?
- **P03 — Relate Poles to Visible Motion:** What inputs, observable effects, and failure modes matter when you relate Poles to Visible Motion?
- **P04 — Compare Linear and Nonlinear Pendulum Models:** What inputs, observable effects, and failure modes matter when you compare Linear and Nonlinear Pendulum Models?

### Phase 2: Feedback fundamentals

- **P05 — Close a Loop with Proportional Control:** What inputs, observable effects, and failure modes matter when you close a Loop with Proportional Control?
- **P06 — Tune a PID by Observing Each Term:** What inputs, observable effects, and failure modes matter when you tune a PID by Observing Each Term?
- **P07 — See Stability Margin in Time and Frequency:** What inputs, observable effects, and failure modes matter when you see Stability Margin in Time and Frequency?
- **P08 — Reject a Disturbance with Feedback:** What inputs, observable effects, and failure modes matter when you reject a Disturbance with Feedback?

### Phase 3: Digital and constrained control

- **P09 — Discretize a Continuous Controller:** What inputs, observable effects, and failure modes matter when you discretize a Continuous Controller?
- **P10 — Expose Delay and Sampling Limits:** What inputs, observable effects, and failure modes matter when you expose Delay and Sampling Limits?
- **P11 — Drive an Actuator into Saturation:** What inputs, observable effects, and failure modes matter when you drive an Actuator into Saturation?
- **P12 — Recover from Integrator Windup:** What inputs, observable effects, and failure modes matter when you recover from Integrator Windup?

### Phase 4: State-space control

- **P13 — Test Controllability:** What inputs, observable effects, and failure modes matter when you test Controllability?
- **P14 — Test Observability:** What inputs, observable effects, and failure modes matter when you test Observability?
- **P15 — Build a State Observer:** What inputs, observable effects, and failure modes matter when you build a State Observer?
- **P16 — Fuse Noisy Sensors with a Kalman Filter:** What inputs, observable effects, and failure modes matter when you fuse Noisy Sensors with a Kalman Filter?

### Phase 5: Optimal and robust control

- **P17 — Balance State Error and Control Effort with LQR:** What inputs, observable effects, and failure modes matter when you balance State Error and Control Effort with LQR?
- **P18 — Use Feedforward and Feedback Together:** What inputs, observable effects, and failure modes matter when you use Feedforward and Feedback Together?
- **P19 — Measure Sensitivity to Model Error:** What inputs, observable effects, and failure modes matter when you measure Sensitivity to Model Error?
- **P20 — Compare Nominal and Robust Designs:** What inputs, observable effects, and failure modes matter when you compare Nominal and Robust Designs?

### Phase 6: Guidance and HIL

- **P21 — Generate a Feasible Trajectory:** What inputs, observable effects, and failure modes matter when you generate a Feasible Trajectory?
- **P22 — Implement Proportional Navigation:** What inputs, observable effects, and failure modes matter when you implement Proportional Navigation?
- **P23 — Model Sensor and Actuator Dynamics:** What inputs, observable effects, and failure modes matter when you model Sensor and Actuator Dynamics?
- **P24 — Close the Loop Through a Hardware-in-the-Loop Plant:** What inputs, observable effects, and failure modes matter when you close the Loop Through a Hardware-in-the-Loop Plant?

## Batch readiness gates

A scaffold may become `implemented` only when it has a deterministic model, a sectioned experiment, two independent parameter sweeps, one deliberately broken case, interactive controls, interpretation-focused tutor text, numerical checks, focused static tests, and evidence that says exactly what did and did not run.
