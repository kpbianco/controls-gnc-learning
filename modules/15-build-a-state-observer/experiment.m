%% P15 - Build a State Observer
%
% Guiding question:
% What inputs, observable effects, and failure modes matter when you build a State Observer?
%
% Run one section at a time. Read the model, inspect the baseline, move one
% lever, inspect its changed view, then reset before moving the next.

%% Read - predict state from a model, known input, and measured position
% P14 established that position history makes both cart states observable.
% P15 turns that structural fact into a running estimate:
%   x[k+1]    = Ad*x[k]    + Bd*u[k]
%   xhat[k+1] = Ad*xhat[k] + Bd*u[k] + L*(y[k]-C*xhat[k])
% The innovation y-C*xhat is the measured disagreement. Predict once: when
% the initial position and rate guesses are wrong, will that disagreement
% drive both errors toward zero even though only position is measured?
observerPoleSpeedPerSec = 2;          % 1/s
interferenceAmplitudeM = 0;           % m
sensorBiasM = 0;                      % m
commandAccelerationMPerSec2 = 0.4;    % m/s^2 after 0.5 s
simulationDurationSec = 8;            % s
timeStepSec = 0.02;                   % s
baseline = model(observerPoleSpeedPerSec,interferenceAmplitudeM, ...
    sensorBiasM,commandAccelerationMPerSec2,simulationDurationSec,timeStepSec);

%% Visualize baseline - unmeasured rate converges from position innovation
figure('Name','P15 baseline state observer');
subplot(2,1,1);
plot(baseline.timeSec,baseline.trueState(1,:), ...
    'LineWidth',1.8,'DisplayName','True position');
hold on;
plot(baseline.timeSec,baseline.estimatedState(1,:),'--', ...
    'LineWidth',1.6,'DisplayName','Estimated position');
hold off; grid on;
xlabel('Time (s)'); ylabel('Position (m)');
title('Position estimate follows the measured state');
legend('Location','best');
subplot(2,1,2);
plot(baseline.timeSec,baseline.trueState(2,:), ...
    'LineWidth',1.8,'DisplayName','True rate');
hold on;
plot(baseline.timeSec,baseline.estimatedState(2,:),'--', ...
    'LineWidth',1.6,'DisplayName','Estimated rate');
hold off; grid on;
xlabel('Time (s)'); ylabel('Rate (m/s)');
title('Rate is reconstructed without a rate measurement');
legend('Location','best');

%% Changed view - inspect innovation and normalized state error
figure('Name','P15 baseline correction signals');
subplot(2,1,1);
plot(baseline.timeSec,baseline.innovationM,'LineWidth',1.8);
grid on; xlabel('Time (s)'); ylabel('Innovation (m)');
title('Measured disagreement drives the correction');
subplot(2,1,2);
semilogy(baseline.timeSec,max(baseline.normalizedErrorNorm,1e-12), ...
    'LineWidth',1.8);
grid on; xlabel('Time (s)'); ylabel('Normalized state-error norm');
title('Matched model, known input, and calibrated sensor make error decay');
fprintf(['Baseline metrics: repeated error pole %.6f per sample; final normalized error %.3g; ' ...
    'last-second position RMS %.3g m; rate RMS %.3g m/s; peak innovation %.3g m.\n'], ...
    baseline.desiredErrorPole,baseline.finalNormalizedError, ...
    baseline.positionErrorRmsTailM,baseline.rateErrorRmsTailMPerSec, ...
    baseline.peakInnovationM);

%% Sweep 1 - move only observer pole speed
observerPoleSpeedsPerSec = [1 2 3 4];
speedFinalErrors = zeros(size(observerPoleSpeedsPerSec));
speedCorrectionGains = zeros(size(observerPoleSpeedsPerSec));
speedPoles = zeros(size(observerPoleSpeedsPerSec));
for k = 1:numel(observerPoleSpeedsPerSec)
    changed = model(observerPoleSpeedsPerSec(k),0,0,0.4,8,0.02);
    speedFinalErrors(k) = changed.finalNormalizedError;
    speedCorrectionGains(k) = norm(changed.normalizedObserverGain);
    speedPoles(k) = changed.desiredErrorPole;
end
figure('Name','P15 observer-speed sweep');
yyaxis left;
semilogy(observerPoleSpeedsPerSec,speedFinalErrors,'o-', ...
    'LineWidth',1.8);
ylabel('Final normalized state-error norm');
yyaxis right;
plot(observerPoleSpeedsPerSec,speedCorrectionGains,'s--', ...
    'LineWidth',1.8);
ylabel('Observer-gain norm (normalized)');
grid on; xlabel('Observer pole speed (1/s)');
title('Faster requested decay needs stronger innovation correction');

%% Read and explain sweep 1 - the pole moves, but correction grows
% The repeated error pole is q=exp(-observerPoleSpeed*dt). Increasing pole
% speed moves q farther inside the unit circle, so the fixed-horizon error
% is smaller in this sweep. The hand-derived L grows because each position
% innovation must produce a stronger position and rate correction. This is
% an observed design tradeoff, not a promise that every transient is monotone.

%% Sweep 2 - reset speed, move only deterministic interference amplitude
interferenceAmplitudesM = [0 0.005 0.02 0.05];
noisePositionRmsM = zeros(size(interferenceAmplitudesM));
noiseRateRmsMPerSec = zeros(size(interferenceAmplitudesM));
for k = 1:numel(interferenceAmplitudesM)
    changed = model(2,interferenceAmplitudesM(k),0,0.4,8,0.02);
    noisePositionRmsM(k) = changed.positionErrorRmsTailM;
    noiseRateRmsMPerSec(k) = changed.rateErrorRmsTailMPerSec;
end
figure('Name','P15 measurement-interference sweep');
plot(interferenceAmplitudesM,noisePositionRmsM,'o-', ...
    'LineWidth',1.8,'DisplayName','Position-error RMS');
hold on;
plot(interferenceAmplitudesM,noiseRateRmsMPerSec,'s--', ...
    'LineWidth',1.8,'DisplayName','Rate-error RMS');
hold off; grid on;
xlabel('Measurement interference amplitude (m)');
ylabel('Last-second estimation-error RMS');
title('Innovation correction also passes measurement interference');
legend('Location','best');

%% Read and explain sweep 2 - correction cannot identify interference
% The true state, input, observer pole, initial estimate, duration, and
% sample interval were reset for every run. Only a deterministic 2.5 Hz
% position-sensor disturbance changed. The observer treats it as genuine
% position disagreement, so both estimated states acquire ripple. This is
% deterministic interference, not stochastic Kalman-filter evidence.

%% Broken case - violate the calibrated-sensor assumption
broken = model(2,0,0.15,0.4,8,0.02);
recovered = model(2,0,0,0.4,8,0.02);
figure('Name','P15 broken biased-sensor case');
subplot(2,1,1);
plot(broken.timeSec,broken.estimationError(1,:), ...
    'LineWidth',1.8,'DisplayName','Position error');
hold on;
yline(-broken.sensorBiasM,'--','Expected -bias limit', ...
    'LineWidth',1.4);
hold off; grid on;
xlabel('Time (s)'); ylabel('True - estimated position (m)');
title('A positive sensor bias makes estimated position too high');
legend('Location','best');
subplot(2,1,2);
plot(broken.timeSec,broken.innovationM,'LineWidth',1.8);
grid on; xlabel('Time (s)'); ylabel('Innovation (m)');
title('Broken symptom: innovation becomes quiet while position stays wrong');
fprintf(['Broken bias: final position error %.3f m; final innovation %.3g m. ' ...
    'Recovered final normalized error %.3g.\n'], ...
    broken.estimationError(1,end),broken.innovationM(end), ...
    recovered.finalNormalizedError);

%% Read and explain the broken mechanism
% P14 observability and stable observer poles assume the measurement means
% what C*x says it means. With y=position+0.15 m, the observer can make the
% innovation nearly zero by estimating position 0.15 m too high. A quiet
% residual therefore does not prove an unbiased state estimate. Restoring
% sensorBiasM to zero recovers the baseline in a fresh, isolated call.

%% Check and teach back
run_checks;
% Then answer in two sentences: name the model, known command, measurement,
% initial estimate, and gain as inputs; describe the visible convergence and
% interference tradeoff; and explain why sensor bias can hide behind a quiet
% innovation. Avoid explaining the lesson as a sequence of MATLAB commands.
