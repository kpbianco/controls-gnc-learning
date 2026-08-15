%% P12 - Recover from Integrator Windup
% Guiding question:
% What inputs, observable effects, and failure modes matter when you recover from Integrator Windup?
%
% P11 showed that requested control can exceed applied actuator effort. A PI
% controller adds memory: I integrates tracking error even while the actuator
% is pinned. That stored effort is windup, and it can keep the command moving
% in the old direction after the target changes.

%% Observe the deterministic baseline
% Run experiment one section at a time. Before the first plot, predict which
% path will reverse its applied command first after the reference changes
% from +2 output to -0.5 output.
experiment;

%% Move one lever at a time
% Sweep anti-windup gain first while high-demand duration stays at 3 s. Then
% reset Kaw to 1 1/s and sweep only demand duration. The first lever changes
% how quickly unavailable effort is removed; the second changes how much time
% the unprotected integrator has to accumulate error.

%% Explain the mechanism from the observed command gap
% The transparent back-calculation equation is
% dI/dt = Ki*e + Kaw*(uApplied-uRequested).
% During positive saturation, uApplied-uRequested is negative. Correctly
% signed feedback therefore opposes the positive Ki*e contribution. It does
% not create actuator authority; it keeps controller memory consistent with
% the effort that actually reached the P11 actuator.

%% Break, recover, check, and teach back
% The broken case flips the command-gap sign. Watch the integral state grow
% and the output remain on the wrong side after the target reverses. Restore
% the sign, run run_checks, then give the two-sentence teach-back requested in
% checks.md before recording personal completion.
