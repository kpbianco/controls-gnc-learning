# P18 walkthrough: Use Feedforward and Feedback Together

## Learner sequence

1. Read the guiding question and the command mixer before running code.
2. Predict only which component reacts when the fixed load begins at `4 s`.
3. Visualize the baseline reference and actual position. They coincide before the load; feedback then
   corrects the tracking error and returns it to the labeled tolerance.
4. View feedforward, feedback, total command, and external disturbance separately. Verify visually
   that total command is the sum of the first two, not the disturbance.
5. Remove the disturbance and sweep only feedforward scale `alpha`. Observe that the changed view has
   exactly zero nominal tracking error and feedback correction at `alpha=1`.
6. Explain the result from `B*(1-alpha)*u_plan` in the error recurrence, not from MATLAB syntax.
7. Reset `alpha=1`, restore the `0.4 m/s^2` load, and sweep only feedback scale `beta`. At zero, the
   load leaves a position offset; positive scales trade correction effort for less error and recovery.
8. Explain the change from the poles of `A-beta*B*K` and the error signal that drives feedback.
9. Reverse feedforward polarity. Identify the large opposing command components as the symptom of a
   violated sign convention, then restore correct polarity and recover the exact baseline.
10. Run `run_module_checks("P18")`, answer one interpretation prompt at a time, and give the required
    two-sentence teach-back.

No MATLAB-runtime or rendered-UI evidence is claimed by this source walkthrough.
