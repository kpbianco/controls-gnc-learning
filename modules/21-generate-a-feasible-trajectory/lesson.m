%% P21 - Generate a Feasible Trajectory
% Guiding question:
% What inputs, observable effects, and failure modes matter when you generate a Feasible Trajectory?

%% Read the constraint contract before plotting a path
% P20 showed that a design label is meaningful only over declared limits.
% P21 generates a rest-to-rest quintic reference, then checks its exact
% peak speed and acceleration against named kinematic constraints.

%% Run the ordered experiment
experiment;

%% Explore one lever at a time
% Run interactive.m. Change target position, reset, then change duration.
% Tighten a constraint only after predicting whether the path itself changes.

%% Explain, check, and teach back
% Run run_checks.m, answer checks.md one prompt at a time, and give the
% required two-sentence teach-back. A feasible kinematic reference is not
% evidence that a real or simulated controlled plant can track it.
