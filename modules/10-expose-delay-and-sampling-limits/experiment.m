%% P10 - Expose Delay and Sampling Limits
%
% Guiding question:
% What inputs, observable effects, and failure modes matter when you expose Delay and Sampling Limits?
%
% Run one section at a time. Observe each changed view before reading the
% mechanism. Reset the first lever before moving the second.

%% Read - separate controller timing from plant motion
% P09 showed that a digital controller samples and holds. P10 adds a compute
% interval Td: after each sample, the actuator continues using the previous
% command until the new command is ready. The plant y'=-y+u never pauses.
% Predict whether delay first appears as a shifted command or a changed output.
samplePeriodSec = 0.05;               % Ts (s)
computationDelaySec = 0.01;           % Td (s)
tEnd = 4;                             % observation duration (s)
displayStepSec = 0.005;               % display grid only (s)
baseline = model(samplePeriodSec,computationDelaySec,tEnd,displayStepSec);

%% Visualize baseline - compare with immediate continuous feedback
figure('Name','P10 baseline output');
plot(baseline.t,baseline.continuousOutput,'k--','LineWidth',1.3, ...
    'DisplayName','Immediate continuous P target');
hold on;
plot(baseline.t,baseline.sampledOutput,'LineWidth',1.7, ...
    'DisplayName','Sampled and delayed output');
plot(baseline.sampleTimes,baseline.outputSamples,'o', ...
    'MarkerSize',3,'DisplayName','Controller samples');
hold off; grid on;
xlabel('Time (s)'); ylabel('Plant output y (output)');
title('Baseline: Ts = 0.05 s and Td = 0.01 s');
legend('Location','best');

%% Changed view - reveal what the actuator actually receives
figure('Name','P10 baseline command timing');
stairs(baseline.t,baseline.computedCommand,'--','LineWidth',1.3, ...
    'DisplayName','Newly computed command');
hold on;
stairs(baseline.t,baseline.appliedCommand,'LineWidth',1.7, ...
    'DisplayName','Command applied after Td');
hold off; grid on;
xlabel('Time (s)'); ylabel('Control effort u (output)');
title('The previous command remains applied while computation is in progress');
legend('Location','best');
fprintf(['Baseline metrics: Ts %.3f s, Td %.3f s (%.0f%% of Ts), ' ...
    'sample rate %.1f (Hz), bandwidth %.3f (Hz), 9 (rad/s), Nyquist ratio %.2f, ' ...
    'delay phase %.1f deg, max gap %.4f output, ' ...
    'pole magnitude %.4f.\n'],baseline.samplePeriodSec, ...
    baseline.computationDelaySec,100*baseline.delayFraction, ...
    baseline.sampleRateHz,baseline.closedLoopBandwidthHz, ...
    baseline.nyquistRatio,baseline.delayPhaseAtBandwidthDeg, ...
    baseline.maximumAbsTrackingGap,baseline.spectralRadius);

%% Read and explain the baseline mechanism
% Each interval has two exact pieces. For Td seconds, y moves under the stale
% command. For Ts-Td seconds, it moves under the new command. The weights are
% wOld=exp(-(Ts-Td))*(1-exp(-Td)) and wNew=1-exp(-(Ts-Td)). Delay does not
% freeze the plant; it spends part of the feedback interval moving on old data.

%% Sweep 1 - move only sample period with zero computation delay
samplePeriodsSec = [0.02 0.05 0.1 0.15 0.2];
figure('Name','P10 sweep 1 - sample period'); hold on; grid on;
for k = 1:numel(samplePeriodsSec)
    changed = model(samplePeriodsSec(k),0,3,0.005);
    plot(changed.t,changed.sampledOutput,'LineWidth',1.2, ...
        'DisplayName',sprintf('Ts=%.2f s, gap=%.3f, |p|max=%.3f', ...
        changed.samplePeriodSec,changed.maximumAbsTrackingGap, ...
        changed.spectralRadius));
end
referenceCase = model(0.05,0,3,0.005);
plot(referenceCase.t,referenceCase.continuousOutput,'k--','LineWidth',1.3, ...
    'DisplayName','Immediate continuous P target');
xlabel('Time (s)'); ylabel('Plant output y (output)');
title('Sweep 1: coarser sampling holds each feedback correction longer');
legend('Location','best');

%% Changed view - sample-period error and stability metrics
sampleGap = zeros(size(samplePeriodsSec));
samplePoleMagnitude = zeros(size(samplePeriodsSec));
sampleNyquistRatio = zeros(size(samplePeriodsSec));
for k = 1:numel(samplePeriodsSec)
    changed = model(samplePeriodsSec(k),0,3,0.005);
    sampleGap(k) = changed.maximumAbsTrackingGap;
    samplePoleMagnitude(k) = changed.spectralRadius;
    sampleNyquistRatio(k) = changed.nyquistRatio;
end
figure('Name','P10 sample-period sweep metrics');
subplot(2,1,1);
plot(samplePeriodsSec,sampleGap,'o-','LineWidth',1.4); grid on;
xlabel('Sample period Ts (s)'); ylabel('Maximum target gap (output)');
title('Less frequent correction increases the continuous-target gap');
subplot(2,1,2);
plot(samplePeriodsSec,samplePoleMagnitude,'s-','LineWidth',1.4); grid on;
hold on; yline(1,'r:','Stability boundary'); hold off;
xlabel('Sample period Ts (s)'); ylabel('Maximum pole magnitude (dimensionless)');
title('Feedback stability can erode before a signal violates Nyquist');

%% Read and explain sweep 1
% Only Ts moved; Td stayed zero and Kp=8 stayed fixed. A longer hold lets one
% correction act after its sampled error is already stale. Nyquist ratio is a
% signal-reconstruction clue, not a guarantee that feedback poles stay inside
% the unit circle.

%% Sweep 2 - reset Ts and move only computation delay
samplePeriodSec = 0.1;
computationDelaysSec = [0 0.02 0.04 0.06 0.08 0.1];
figure('Name','P10 sweep 2 - computation delay'); hold on; grid on;
for k = 1:numel(computationDelaysSec)
    changed = model(samplePeriodSec,computationDelaysSec(k),4,0.005);
    plot(changed.t,changed.sampledOutput,'LineWidth',1.2, ...
        'DisplayName',sprintf('Td=%.2f s, delay=%.0f%%, |p|max=%.3f', ...
        changed.computationDelaySec,100*changed.delayFraction, ...
        changed.spectralRadius));
end
xlabel('Time (s)'); ylabel('Plant output y (output)');
title('Sweep 2: stale-command time adds oscillation and overshoot');
legend('Location','best');

%% Changed view - delay phase and pole movement
delayPhaseDeg = zeros(size(computationDelaysSec));
delayPoleMagnitude = zeros(size(computationDelaysSec));
delayOvershootPercent = zeros(size(computationDelaysSec));
for k = 1:numel(computationDelaysSec)
    changed = model(samplePeriodSec,computationDelaysSec(k),4,0.005);
    delayPhaseDeg(k) = changed.delayPhaseAtBandwidthDeg;
    delayPoleMagnitude(k) = changed.spectralRadius;
    delayOvershootPercent(k) = changed.overshootPercent;
end
figure('Name','P10 delay sweep metrics');
subplot(2,1,1);
plot(computationDelaysSec,delayPhaseDeg,'o-','LineWidth',1.4); grid on;
xlabel('Computation delay Td (s)');
ylabel('Delay phase at 9 rad/s (deg)');
title('More latency consumes phase before the command reaches the plant');
subplot(2,1,2);
plot(computationDelaysSec,delayPoleMagnitude,'s-','LineWidth',1.4); grid on;
hold on; yline(1,'r:','Stability boundary'); hold off;
xlabel('Computation delay Td (s)');
ylabel('Maximum pole magnitude (dimensionless)');
title('The same sample rate can have a different stability reserve');

%% Read and explain sweep 2
% Ts reset to 0.1 s. Only Td moved. Increasing Td transfers more of each
% interval from the new-command weight to the previous-command weight. The
% actuator therefore spends longer acting on an older output measurement,
% which raises overshoot and pole magnitude without changing sample rate.

%% Broken case - combine a long hold with nearly one-sample delay
% Ts=0.2 s still samples the 9 rad/s continuous bandwidth above its Nyquist
% rate, yet Td=0.18 s leaves only 0.02 s for each new correction. The exact
% two-state pole magnitude exceeds one, so oscillations grow. Nyquist alone
% did not account for feedback latency.
broken = model(0.2,0.18,3,0.005);
recovered = model(0.2,0.02,3,0.005);
figure('Name','P10 broken delay and recovery');
subplot(2,1,1);
plot(broken.t,broken.sampledOutput,'LineWidth',1.6, ...
    'DisplayName','Broken output');
hold on; plot(broken.t,broken.continuousOutput,'k--', ...
    'DisplayName','Immediate continuous target'); hold off; grid on;
xlabel('Time (s)'); ylabel('Plant output y (output)');
title(sprintf('Broken: Ts=0.20 s, Td=0.18 s, pole magnitude %.3f', ...
    broken.spectralRadius));
legend('Location','best');
subplot(2,1,2);
plot(recovered.t,recovered.sampledOutput,'LineWidth',1.6, ...
    'DisplayName','Recovered output');
hold on; plot(recovered.t,recovered.continuousOutput,'k--', ...
    'DisplayName','Immediate continuous target'); hold off; grid on;
xlabel('Time (s)'); ylabel('Plant output y (output)');
title(sprintf('Recovery: same Ts, Td=0.02 s, pole magnitude %.3f', ...
    recovered.spectralRadius));
legend('Location','best');
fprintf(['Broken Nyquist ratio %.2f and pole magnitude %.4f; ' ...
    'same-Ts recovery pole magnitude %.4f and final deviation %.6f output.\n'], ...
    broken.nyquistRatio,broken.spectralRadius,recovered.spectralRadius, ...
    recovered.finalEquilibriumDeviation);

%% Read and explain recovery
% The failure violates the assumption that sensing, computation, and actuation
% finish early enough within each feedback interval. Reducing only Td preserves
% Ts, Kp, plant, and reference while moving both poles inside the unit circle.
% A faster processor or scheduled computation can recover delay reserve; drawing
% a smoother line through samples cannot change the command the plant received.
