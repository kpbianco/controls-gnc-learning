# P21 checks: Generate a Feasible Trajectory

Run `run_module_checks("P21")`, then answer one prompt at a time:

1. Why can a trajectory meet its endpoint position, speed, and acceleration conditions yet still be infeasible?
2. Why does doubling duration divide peak speed by two, peak acceleration by four, and peak jerk by eight?
3. Why must feasibility use analytic peaks rather than only the largest value on a plot grid?
4. What do target position, duration, speed limit, and acceleration limit each change, and which changes the
   polynomial path rather than only its verdict?
5. What additional plant, obstacle, actuator, and feedback evidence would be needed before calling the move
   trackable or safe?

## Teach-back

In exactly two sentences, name the trajectory inputs and the observable time-scaling effects. Then state the
speed/acceleration feasibility rule and explain why the smooth `4 s` request fails.

The source and independent oracle provide static and simulated evidence only. No MATLAB-runtime,
rendered-UI, numerical-fidelity, plant-tracking, bench, HIL, field, or production validation is claimed.
