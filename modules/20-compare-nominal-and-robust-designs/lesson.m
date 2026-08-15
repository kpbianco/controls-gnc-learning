%% P20 - Compare Nominal and Robust Designs
% Guiding question:
% What inputs, observable effects, and failure modes matter when you compare Nominal and Robust Designs?

%% Read the comparison contract before running plots
% P19 exposed actuator-gain and drag sensitivity for one fixed controller.
% P20 compares matched-plant tracking with worst-case tracking over a named
% positive uncertainty grid and an explicit command-effort constraint.

%% Run the ordered experiment
experiment;

%% Explore one uncertainty at a time
% Run interactive.m. Move actuator gain ratio, reset, then move drag ratio.
% Use reversed polarity only after identifying the finite-grid tradeoff.

%% Explain, check, and teach back
% Run run_checks.m, answer checks.md one prompt at a time, and give the
% required two-sentence teach-back. Source and independent reference
% simulation do not establish MATLAB-runtime or physical validation.
