%% P15 - Build a State Observer
% Guiding question:
% What inputs, observable effects, and failure modes matter when you build a State Observer?
%
% P14 proved that position history reveals the cart's position and rate.
% P15 closes an estimation-error loop around that observable measurement.

%% Observe the deterministic baseline
% Run experiment one section at a time. Before the baseline error plot,
% predict whether position innovation can correct an unmeasured rate error.
experiment;

%% Move one lever at a time
% Sweep observer pole speed with zero interference and zero bias. Then reset
% pole speed to 2 1/s and sweep only deterministic position interference.
% Faster correction reduces fixed-horizon error but needs more gain; sensor
% disturbance enters through the same correction path as useful information.

%% Explain the mechanism from the visible recurrence
% With matched dynamics, a known input, and calibrated measurement,
%   error[k+1] = (Ad-L*C)*error[k] - L*interference[k].
% The known command cancels because plant and observer both receive it. The
% requested pole controls decay; L controls how strongly measurement error
% changes the two estimated states.

%% Break, recover, check, and teach back
% Add +0.15 m sensor bias. The innovation becomes quiet after the observer
% estimates position too high, so a small residual is not proof of accuracy.
% Restore zero bias, run run_checks, then give the two-sentence teach-back in
% checks.md without describing MATLAB syntax as the governing mechanism.
