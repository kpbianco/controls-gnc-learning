%% P22 - Implement Proportional Navigation
% Guiding question:
% What inputs, observable effects, and failure modes matter when you implement Proportional Navigation?

%% Read the relative-guidance contract before plotting an engagement
% P21 checked whether a reference fit kinematic limits. P22 uses relative
% position and velocity to compute closing speed, LOS rate, and a transparent
% lateral command, then checks whether acceleration authority can apply it.

%% Run the ordered experiment
experiment;

%% Explore one lever at a time
% Run interactive.m. Change N, reset, then change acceleration authority.
% Change target crossing speed only after explaining which LOS term it moves.

%% Explain, check, and teach back
% Run run_checks.m, answer checks.md one prompt at a time, and give the
% required two-sentence teach-back. Capture in this sampled point-mass model
% is not evidence of autopilot, actuator, HIL, or physical interception.
