# P19 walkthrough: Measure Sensitivity to Model Error

## Learner sequence

1. Read the guiding question and the speed-plant equation before running code.
2. Predict only whether a `20%` weaker actuator puts measured steady speed above or below prediction.
3. Visualize the baseline reference, nominal prediction, and actual speed. Confirm that matched
   parameters give an exactly zero prediction-gap history.
4. View nominal and actual command histories. At the matched limit they coincide; model error makes
   feedback request a different correction.
5. Sweep only actuator gain ratio. Observe the direction of steady-speed change, then read the local
   sensitivity as output speed per unit fractional gain error.
6. Explain the changed view from actuator effectiveness in both numerator and denominator of the
   equilibrium quotient, not from MATLAB syntax.
7. Reset actuator gain to one and sweep only drag ratio. Observe the opposite sensitivity sign while
   reference, controller, sign, duration, and time grid remain fixed.
8. Explain why extra drag lowers speed from the same quotient and why the prediction-gap RMSE is zero
   only at the matched ratio.
9. Reverse actuator polarity. Identify the pole magnitude above one and growing correction as a
   structural failure, then restore correct polarity and recover the exact baseline.
10. Run `run_module_checks("P19")`, answer one interpretation prompt at a time, and give the required
    two-sentence teach-back.

No MATLAB-runtime, rendered-UI, or physical evidence is claimed by this source walkthrough.
