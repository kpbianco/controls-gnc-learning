%% Read: a guidance request is not instantaneous motion or measurement
% P22 produced lateral-acceleration requests from relative geometry. P23
% puts two physical states after that request: tau_a*a_dot+a=u for the
% actuator and tau_s*y_dot+y=a for the sensor. The output chain is therefore
% requested u -> limited command -> actual a -> measured y+bias.

%% Make one prediction before the baseline
% After the first command reversal, which curve changes sign last: the
% requested acceleration, the applied acceleration, or the measurement?

%% Visualize the deterministic baseline
baseline = model(0.2,0.1,2,20,30,0,0.02,8);
fprintf(['Baseline: actuator RMS error %.3f m/s^2, sensor dynamic RMS ' ...
    'error %.3f m/s^2, opposite-sign time %.3f s, saturation %.3f s.\n'], ...
    baseline.actuatorTrackingRmsMPerSec2, ...
    baseline.sensorDynamicRmsMPerSec2, ...
    baseline.oppositeSignDurationSec,baseline.saturationDurationSec);

figure('Name','P23 baseline acceleration chain');
plot(baseline.timeSec,baseline.requestedAccelerationMPerSec2,'k--', ...
    'LineWidth',1.4,'DisplayName','Requested acceleration');
hold on;
plot(baseline.timeSec,baseline.actualAccelerationMPerSec2,'b-', ...
    'LineWidth',1.8,'DisplayName','Applied acceleration');
plot(baseline.timeSec,baseline.measuredAccelerationMPerSec2,'m-', ...
    'LineWidth',1.6,'DisplayName','Measured acceleration');
yline(baseline.actuatorLimitMPerSec2,'r:', ...
    'Positive actuator limit');
yline(-baseline.actuatorLimitMPerSec2,'r:', ...
    'Negative actuator limit');
hold off; grid on;
xlabel('Time (s)'); ylabel('Lateral acceleration (m/s^2)');
title('Baseline: actuator motion precedes the sensor report');
legend('Location','best');

figure('Name','P23 baseline dynamic errors');
subplot(2,1,1);
plot(baseline.timeSec,baseline.actuatorTrackingErrorMPerSec2,'b-', ...
    'LineWidth',1.7);
grid on; xlabel('Time (s)');
ylabel('Request - applied (m/s^2)');
title('Actuator lag is largest just after a reversal');
subplot(2,1,2);
plot(baseline.timeSec,baseline.sensorDynamicErrorMPerSec2,'m-', ...
    'LineWidth',1.7);
grid on; xlabel('Time (s)');
ylabel('Applied - sensed (m/s^2)');
title('Complementary view: the sensor adds another lag');

%% Read the mechanism: each time constant stores its own history
% Over one held-input interval, the model uses exp(-dt/tau), not a toolbox
% block. A larger tau retains more of the previous state. The actuator must
% move before the sensor can report that motion, and a static sensor bias is
% added only after the dynamic state.

%% Move lever 1: sweep only sensor time constant
% Actuator tau, request timing, amplitude, limit, bias, step, and duration
% reset on every call. The actual motion must remain exactly unchanged.
sensorTimeConstantValuesSec = [0 0.02 0.05 0.1 0.2 0.4];
sensorRmsErrorMPerSec2 = zeros(size(sensorTimeConstantValuesSec));
sensorOppositeSignDurationSec = zeros(size(sensorTimeConstantValuesSec));
sensorFirstPlateauMPerSec2 = zeros(size(sensorTimeConstantValuesSec));
for k = 1:numel(sensorTimeConstantValuesSec)
    changed = model(0.2,sensorTimeConstantValuesSec(k),2,20,30,0,0.02,8);
    assert(changed.actuatorTimeConstantSec == 0.2 && ...
        changed.commandHalfPeriodSec == 2 && ...
        changed.commandAmplitudeMPerSec2 == 20 && ...
        changed.actuatorLimitMPerSec2 == 30 && ...
        changed.sensorBiasMPerSec2 == 0 && ...
        changed.timeStepSec == 0.02 && changed.durationSec == 8, ...
        'Sensor sweep changed a non-swept input.');
    assert(isequal(changed.actualAccelerationMPerSec2, ...
        baseline.actualAccelerationMPerSec2), ...
        'Sensor dynamics must not alter upstream actuator motion.');
    sensorRmsErrorMPerSec2(k) = changed.sensorDynamicRmsMPerSec2;
    sensorOppositeSignDurationSec(k) = changed.oppositeSignDurationSec;
    sensorFirstPlateauMPerSec2(k) = changed.firstPlateauMeasuredMPerSec2;
end
figure('Name','P23 sensor-time-constant sweep');
subplot(3,1,1);
plot(sensorTimeConstantValuesSec,sensorRmsErrorMPerSec2,'mo-', ...
    'LineWidth',1.7); grid on;
xlabel('Sensor time constant (s)');
ylabel('Sensor RMS error (m/s^2)');
title('Sweep 1 changed view: slower sensing increases mismatch');
subplot(3,1,2);
plot(sensorTimeConstantValuesSec,sensorOppositeSignDurationSec,'ks-', ...
    'LineWidth',1.7); grid on;
xlabel('Sensor time constant (s)'); ylabel('Opposite-sign time (s)');
title('A stale measurement can retain the old turn sign');
subplot(3,1,3);
plot(sensorTimeConstantValuesSec,sensorFirstPlateauMPerSec2,'bd-', ...
    'LineWidth',1.7);
hold on; yline(20,'k:','Requested plateau'); hold off; grid on;
xlabel('Sensor time constant (s)');
ylabel('First-plateau measurement (m/s^2)');
title('Longer sensor memory delays the reported plateau');

%% Explain lever 1 from the sensor state equation
% Increasing tau_s makes exp(-dt/tau_s) closer to one, so more of the old
% measurement remains after every update. Command and actuator histories are
% identical across the sweep; only the sensor view changes.

%% Reset, then move lever 2: sweep only actuator time constant
% Sensor tau returns to 0.1 s. A slower actuator raises request-to-applied
% error before the unchanged sensor adds its own dynamics.
actuatorTimeConstantValuesSec = [0 0.05 0.1 0.2 0.4 0.8];
actuatorRmsErrorMPerSec2 = zeros(size(actuatorTimeConstantValuesSec));
actuatorPeakMPerSec2 = zeros(size(actuatorTimeConstantValuesSec));
actuatorOppositeSignDurationSec = zeros( ...
    size(actuatorTimeConstantValuesSec));
for k = 1:numel(actuatorTimeConstantValuesSec)
    changed = model(actuatorTimeConstantValuesSec(k),0.1,2,20,30,0,0.02,8);
    assert(changed.sensorTimeConstantSec == 0.1 && ...
        changed.commandHalfPeriodSec == 2 && ...
        changed.commandAmplitudeMPerSec2 == 20 && ...
        changed.actuatorLimitMPerSec2 == 30 && ...
        changed.sensorBiasMPerSec2 == 0 && ...
        changed.timeStepSec == 0.02 && changed.durationSec == 8, ...
        'Actuator sweep changed a non-swept input.');
    actuatorRmsErrorMPerSec2(k) = changed.actuatorTrackingRmsMPerSec2;
    actuatorPeakMPerSec2(k) = changed.peakActualAccelerationMPerSec2;
    actuatorOppositeSignDurationSec(k) = ...
        changed.oppositeSignDurationSec;
end
figure('Name','P23 actuator-time-constant sweep');
subplot(3,1,1);
plot(actuatorTimeConstantValuesSec,actuatorRmsErrorMPerSec2,'bo-', ...
    'LineWidth',1.7); grid on;
xlabel('Actuator time constant (s)');
ylabel('Actuator RMS error (m/s^2)');
title('Sweep 2 changed view: slower actuation tracks less closely');
subplot(3,1,2);
plot(actuatorTimeConstantValuesSec,actuatorPeakMPerSec2,'ms-', ...
    'LineWidth',1.7);
hold on; yline(20,'k:','Requested amplitude'); hold off; grid on;
xlabel('Actuator time constant (s)');
ylabel('Peak applied acceleration (m/s^2)');
title('A slow actuator may not reach the requested plateau');
subplot(3,1,3);
plot(actuatorTimeConstantValuesSec, ...
    actuatorOppositeSignDurationSec,'kd-','LineWidth',1.7); grid on;
xlabel('Actuator time constant (s)'); ylabel('Opposite-sign time (s)');
title('Actuator memory propagates downstream to the measurement');

%% Explain lever 2 from command versus applied motion
% Increasing tau_a preserves more of the previous actuator state. It does
% not change the requested command. Saturation is a separate magnitude
% limit: when amplitude exceeds authority, the limited command clips before
% either dynamic state evolves.

%% Deliberately broken case: violate bandwidth separation
% Reversing every 0.1 s while tau_a=0.8 s and tau_s=0.6 s asks both devices
% to follow much faster than their dynamics allow. Applied and measured
% peaks collapse, and the measurement can retain the opposite sign.
broken = model(0.8,0.6,0.1,20,30,0,0.01,4);
bandwidthRecovered = model(0.8,0.6,4,20,30,0,0.01,4);
recovered = model(0.2,0.1,2,20,30,0,0.02,8);
assert(broken.peakActualAccelerationMPerSec2 < 3 && ...
    broken.peakMeasuredAccelerationMPerSec2 < 1 && ...
    broken.oppositeSignDurationSec > 0.5, ...
    'The broken bandwidth case must be attenuated and sign-stale.');
assert(bandwidthRecovered.peakActualAccelerationMPerSec2 > 19 && ...
    bandwidthRecovered.peakMeasuredAccelerationMPerSec2 > 19 && ...
    bandwidthRecovered.oppositeSignDurationSec == 0, ...
    'A longer hold must restore separation for the same slow devices.');
assert(isequaln(recovered,baseline), ...
    'A fresh valid call must exactly recover the baseline.');
figure('Name','P23 broken bandwidth-separation case');
plot(broken.timeSec,broken.requestedAccelerationMPerSec2,'k--', ...
    'LineWidth',1.3,'DisplayName','Requested acceleration');
hold on;
plot(broken.timeSec,broken.actualAccelerationMPerSec2,'b-', ...
    'LineWidth',1.8,'DisplayName','Applied acceleration');
plot(broken.timeSec,broken.measuredAccelerationMPerSec2,'m-', ...
    'LineWidth',1.7,'DisplayName','Measured acceleration');
hold off; grid on;
xlabel('Time (s)'); ylabel('Lateral acceleration (m/s^2)');
title('Broken assumption: requests reverse faster than device bandwidth');
legend('Location','best');

%% Check, recover, and teach back
% Clear a generic run_checks function cached from another module before
% resolving P23's module-local checks on the active path.
clear run_checks;
run_checks;
% Teach back in exactly two sentences: name command timing, actuator tau,
% sensor tau, magnitude limit, and bias; then explain how stored state makes
% applied and measured acceleration lag or contradict a fast request.
