%% P16 - Fuse Noisy Sensors with a Kalman Filter
% Guiding question:
% What inputs, observable effects, and failure modes matter when you fuse Noisy Sensors with a Kalman Filter?
%
% P15 used observable position and fixed innovation feedback. P16 makes
% uncertainty part of the state estimator and fuses two position sensors.

%% Observe the deterministic seeded baseline
% Run experiment one section at a time. Before the baseline, predict which
% position sensor receives more gain when sensor A reports 0.35 m standard
% deviation and sensor B reports 0.8 m.
experiment;

%% Move one lever at a time
% Sweep only sensor A's assumed noise with Q fixed. Reset R, then sweep only
% assumed acceleration noise in Q. Reported measurement uncertainty changes
% sensor trust; reported process uncertainty changes trust in prediction.

%% Explain the mechanism from covariance
% Prediction adds Q to P. Measurement comparison adds R to form S. The gain
% K=Pminus*C'/S grows where predicted state uncertainty is large and falls
% where a sensor reports more uncertainty. The Joseph update records the
% uncertainty remaining after correction.

%% Break, recover, check, and teach back
% Add one +4 m sensor A outlier. It violates the zero-mean covariance model,
% makes normalized innovation squared spike, and still receives a correction
% gain. Restore zero outlier, run run_checks, then give the checks.md
% two-sentence teach-back without treating syntax as the mechanism.
