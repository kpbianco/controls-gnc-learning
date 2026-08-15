%% P16 - Fuse Noisy Sensors with a Kalman Filter
%
% Guiding question:
% What inputs, observable effects, and failure modes matter when you fuse Noisy Sensors with a Kalman Filter?
%
% Run one section at a time. Read the covariance model, inspect the seeded
% baseline, move one lever, inspect its changed view, then reset.

%% Read - predict, compare two sensors, and update uncertainty
% P15 used one innovation with a fixed correction gain. P16 lets the gain
% follow declared uncertainty at every sample:
%   xminus[k] = A*xplus[k-1] + B*u[k-1]
%   Pminus[k] = A*Pplus[k-1]*A' + Q
%   innovation = y - C*xminus
%   K = Pminus*C' * inverse(C*Pminus*C' + R)
%   xplus = xminus + K*innovation
% Sensor A and sensor B both measure position, but A is less noisy. Predict
% once: which sensor should have more influence when its reported standard
% deviation is smaller?
assumedPositionNoiseStdM = 0.35;              % m, sensor A
assumedProcessAccelerationStdMPerSec2 = 0.08; % m/s^2
positionOutlierM = 0;                         % m
noiseSeed = 1601;                             % dimensionless integer
simulationDurationSec = 20;                   % s
timeStepSec = 0.05;                           % s
baseline = model(assumedPositionNoiseStdM, ...
    assumedProcessAccelerationStdMPerSec2,positionOutlierM,noiseSeed, ...
    simulationDurationSec,timeStepSec);

%% Visualize baseline - two noisy positions become one state estimate
figure('Name','P16 baseline sensor fusion');
plot(baseline.timeSec,baseline.measurement(1,:),'.', ...
    'Color',[0.55 0.72 0.95],'DisplayName','Sensor A position');
hold on;
plot(baseline.timeSec,baseline.measurement(2,:),'.', ...
    'Color',[0.85 0.72 0.55],'DisplayName','Sensor B position');
plot(baseline.timeSec,baseline.trueState(1,:),'k-', ...
    'LineWidth',1.8,'DisplayName','True position');
plot(baseline.timeSec,baseline.posteriorEstimate(1,:),'b--', ...
    'LineWidth',1.6,'DisplayName','Fused position');
hold off; grid on;
xlabel('Time (s)'); ylabel('Position (m)');
title('Prediction and two measurements produce one position estimate');
legend('Location','best');

%% Changed view - inspect rate, covariance, and innovation consistency
figure('Name','P16 baseline uncertainty and consistency');
subplot(2,1,1);
plot(baseline.timeSec,baseline.trueState(2,:),'k-', ...
    'LineWidth',1.8,'DisplayName','True rate');
hold on;
plot(baseline.timeSec,baseline.posteriorEstimate(2,:),'b--', ...
    'LineWidth',1.6,'DisplayName','Estimated rate');
plot(baseline.timeSec,baseline.posteriorRateStdMPerSec,'r:', ...
    'LineWidth',1.4,'DisplayName','Reported 1-sigma rate uncertainty');
hold off; grid on;
xlabel('Time (s)'); ylabel('Rate (m/s)');
title('Position histories and the motion model reconstruct rate');
legend('Location','best');
subplot(2,1,2);
plot(baseline.timeSec,baseline.normalizedInnovationSquared, ...
    'LineWidth',1.4);
hold on; yline(9.21,'--','Two-sensor 99% reference'); hold off;
grid on; xlabel('Time (s)');
ylabel('Normalized innovation squared');
title('Innovation is scaled by its predicted covariance');
fprintf(['Baseline metrics: tail position RMSE %.3f m; rate RMSE %.3f m/s; ' ...
    'mean tail NIS %.3f; steady position gains %.4f and %.4f.\n'], ...
    baseline.positionErrorRmsTailM,baseline.rateErrorRmsTailMPerSec, ...
    baseline.meanNormalizedInnovationSquaredTail, ...
    baseline.steadyPrimaryPositionGain,baseline.steadyBackupPositionGain);

%% Sweep 1 - move only sensor A reported noise
assumedPositionNoiseStdValuesM = [0.1 0.2 0.35 0.6 0.9];
primaryPositionGains = zeros(size(assumedPositionNoiseStdValuesM));
backupPositionGains = zeros(size(assumedPositionNoiseStdValuesM));
meanTailNis = zeros(size(assumedPositionNoiseStdValuesM));
for k = 1:numel(assumedPositionNoiseStdValuesM)
    changed = model(assumedPositionNoiseStdValuesM(k),0.08,0,1601,20,0.05);
    primaryPositionGains(k) = changed.steadyPrimaryPositionGain;
    backupPositionGains(k) = changed.steadyBackupPositionGain;
    meanTailNis(k) = changed.meanNormalizedInnovationSquaredTail;
end
figure('Name','P16 sensor-noise sweep');
yyaxis left;
plot(assumedPositionNoiseStdValuesM,primaryPositionGains,'o-', ...
    'LineWidth',1.8,'DisplayName','Sensor A position gain');
hold on;
plot(assumedPositionNoiseStdValuesM,backupPositionGains,'s--', ...
    'LineWidth',1.8,'DisplayName','Sensor B position gain');
hold off; ylabel('Steady position gain (dimensionless)');
yyaxis right;
plot(assumedPositionNoiseStdValuesM,meanTailNis,'d:', ...
    'LineWidth',1.8,'DisplayName','Mean tail NIS');
ylabel('Mean normalized innovation squared');
grid on; xlabel('Assumed sensor A noise standard deviation (m)');
title('Reported sensor noise reallocates trust between two sensors');
legend('Location','best');

%% Read and explain sweep 1 - R reallocates measurement trust
% The true trajectory, seeded noise, process assumption, outlier, duration,
% and sample interval reset on every run. Raising sensor A's reported noise
% increases its R entry, so its gain falls and the filter leans relatively
% more on sensor B and prediction. Under-reporting A's actual 0.35 m noise
% makes normalized innovations look too large for the claimed covariance.

%% Sweep 2 - reset sensor noise, move only process uncertainty
assumedProcessNoiseStdValuesMPerSec2 = [0.01 0.04 0.08 0.2 0.5];
rateGainsPerSec = zeros(size(assumedProcessNoiseStdValuesMPerSec2));
reportedRateStdMPerSec = zeros(size(assumedProcessNoiseStdValuesMPerSec2));
for k = 1:numel(assumedProcessNoiseStdValuesMPerSec2)
    changed = model(0.35,assumedProcessNoiseStdValuesMPerSec2(k), ...
        0,1601,20,0.05);
    rateGainsPerSec(k) = changed.steadyRateGainFromPrimaryPerSec;
    reportedRateStdMPerSec(k) = changed.posteriorRateStdMPerSec(end);
end
figure('Name','P16 process-noise sweep');
yyaxis left;
plot(assumedProcessNoiseStdValuesMPerSec2,rateGainsPerSec,'o-', ...
    'LineWidth',1.8);
ylabel('Rate gain from sensor A (1/s)');
yyaxis right;
plot(assumedProcessNoiseStdValuesMPerSec2,reportedRateStdMPerSec,'s--', ...
    'LineWidth',1.8);
ylabel('Reported rate standard deviation (m/s)');
grid on;
xlabel('Assumed process acceleration standard deviation (m/s^2)');
title('More process uncertainty invites stronger measurement correction');

%% Read and explain sweep 2 - Q trades model confidence for correction
% Raising assumed acceleration noise enlarges Q during prediction. The
% filter reports more rate uncertainty and uses position innovation more
% strongly to correct rate. Q is uncertainty about unmodeled motion, not a
% knob that changes the already seeded physical trajectory in this sweep.

%% Broken case - inject one outlier outside the noise model
broken = model(0.35,0.08,4,1601,20,0.05);
recovered = model(0.35,0.08,0,1601,20,0.05);
figure('Name','P16 broken outlier case');
subplot(2,1,1);
plot(broken.timeSec,broken.estimationError(1,:),'LineWidth',1.8);
hold on; xline(broken.outlierTimeSec,'--','Sensor A outlier'); hold off;
grid on; xlabel('Time (s)');
ylabel('True - estimated position (m)');
title('An unmodeled outlier kicks the fused position estimate');
subplot(2,1,2);
plot(broken.timeSec,broken.normalizedInnovationSquared,'LineWidth',1.4);
hold on; yline(9.21,'--','Two-sensor 99% reference'); hold off;
grid on; xlabel('Time (s)');
ylabel('Normalized innovation squared');
title('Broken symptom: covariance cannot explain the innovation spike');
fprintf(['Broken outlier: NIS at %.2f s is %.1f versus clean %.1f. ' ...
    'Fresh-call recovered tail position RMSE %.3f m.\n'], ...
    broken.outlierTimeSec, ...
    broken.normalizedInnovationSquared(broken.outlierIndex), ...
    recovered.normalizedInnovationSquared(recovered.outlierIndex), ...
    recovered.positionErrorRmsTailM);

%% Read and explain the broken mechanism
% Q and R describe zero-mean, repeatable covariance assumptions. A one-shot
% +4 m sensor A outlier is not represented by that R. Its innovation is far
% larger than S predicts, NIS spikes, and the gain still applies an
% unsupported correction. Robust rejection is not automatic. A fresh
% zero-outlier call recovers the exact baseline without hidden model state.

%% Check and teach back
% Clear any generic run_checks function cached from another module before
% resolving P16's module-local checks on the active path.
clear run_checks;
run_checks;
% Then answer in two sentences: name prediction, both measurements, Q, and
% R; describe how each lever reallocates trust; and explain why an outlier
% makes NIS spike and can move the fused estimate.
