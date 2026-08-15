%% P19 - Measure Sensitivity to Model Error
% Guiding question:
% What inputs, observable effects, and failure modes matter when you measure Sensitivity to Model Error?

%% Read the mechanism before running the plots
% P18 showed why a nominal feedforward command still needs feedback. Here
% the controller stays fixed while the actual actuator gain and drag move
% away from the nominal model. The prediction gap exposes the consequence.

%% Run the ordered experiment
experiment;

%% Explore one uncertainty at a time
% Run interactive.m. Move actuator gain ratio, reset, then move drag ratio.
% Use the reversed-sign choice only after identifying each ordinary model
% error's direction from the speed and sensitivity views.

%% Explain, check, and teach back
% Run run_checks.m, answer checks.md one prompt at a time, and give the
% required two-sentence teach-back. Source and independent reference
% simulation do not establish MATLAB-runtime or physical validation.
