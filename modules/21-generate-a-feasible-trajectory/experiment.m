%% Read: trajectory feasibility means derivative demands fit declared limits
% P20 attached a robustness claim to an explicit set and effort constraint.
% P21 applies that discipline before feedback: generate a transparent
% rest-to-rest quintic reference, then compare its analytic peak speed and
% acceleration with declared limits. Smooth endpoints alone are not enough.

%% Make one prediction before the baseline
% Will a 20 m move completed in 8 s stay inside 5 m/s and 2 m/s^2 limits?

%% Visualize the deterministic baseline
baseline = model(20,8,5,2,501);
fprintf(['Baseline: peak speed %.4f / %.1f m/s; peak acceleration ' ...
    '%.4f / %.1f m/s^2; minimum duration %.4f s; %s.\n'], ...
    baseline.analyticPeakSpeedMPerSec,baseline.maximumSpeedMPerSec, ...
    baseline.analyticPeakAccelerationMPerSec2, ...
    baseline.maximumAccelerationMPerSec2, ...
    baseline.minimumFeasibleDurationSec,baseline.feasibilityStatus);

figure('Name','P21 baseline position and speed');
subplot(2,1,1);
plot(baseline.timeSec,baseline.positionM,'b-','LineWidth',1.8);
grid on;
xlabel('Time (s)'); ylabel('Position (m)');
title('Baseline path: rest-to-rest position reference');
subplot(2,1,2);
plot(baseline.timeSec,baseline.speedMPerSec,'m-','LineWidth',1.8, ...
    'DisplayName','Trajectory speed');
hold on;
yline(baseline.maximumSpeedMPerSec,'r:','Positive speed limit');
yline(-baseline.maximumSpeedMPerSec,'r:','Negative speed limit');
hold off; grid on;
xlabel('Time (s)'); ylabel('Speed (m/s)');
title('Peak speed occurs halfway through the move');
legend('Location','best');

figure('Name','P21 baseline acceleration and feasibility');
subplot(2,1,1);
plot(baseline.timeSec,baseline.accelerationMPerSec2,'c-', ...
    'LineWidth',1.8,'DisplayName','Trajectory acceleration');
hold on;
yline(baseline.maximumAccelerationMPerSec2,'r:', ...
    'Positive acceleration limit');
yline(-baseline.maximumAccelerationMPerSec2,'r:', ...
    'Negative acceleration limit');
hold off; grid on;
xlabel('Time (s)'); ylabel('Acceleration (m/s^2)');
title('Complementary view: acceleration changes sign at midpoint');
legend('Location','best');
subplot(2,1,2);
bar(100*[baseline.speedUtilization baseline.accelerationUtilization]);
hold on; yline(100,'r:','Feasibility boundary'); hold off; grid on;
set(gca,'XTickLabel',{'Speed','Acceleration'});
ylabel('Constraint utilization (%)');
title('Analytic peaks, not plot samples, decide feasibility');

%% Read the mechanism: normalized shape plus time scaling
% With tau=t/T, position is xf*h(tau), speed is xf/T*h'(tau),
% acceleration is xf/T^2*h''(tau), and jerk is xf/T^3*h'''(tau).
% The exact peak formulas provide separate speed- and acceleration-derived
% minimum durations; the larger bound is the active constraint.

%% Move lever 1: sweep only target distance
% Duration, both limits, and the sample grid reset on every call. Absolute
% derivative demand grows linearly with travel distance, while the active
% minimum-duration constraint can change because its bounds scale differently.
targetPositionValuesM = [5 10 15 20 25];
distancePeakSpeedMPerSec = zeros(size(targetPositionValuesM));
distancePeakAccelerationMPerSec2 = zeros(size(targetPositionValuesM));
distanceMinimumDurationSec = zeros(size(targetPositionValuesM));
distanceFeasible = false(size(targetPositionValuesM));
for k = 1:numel(targetPositionValuesM)
    changed = model(targetPositionValuesM(k),8,5,2,501);
    assert(changed.moveDurationSec == 8 && ...
        changed.maximumSpeedMPerSec == 5 && ...
        changed.maximumAccelerationMPerSec2 == 2 && ...
        changed.sampleCount == 501, ...
        'Distance sweep changed a non-swept input.');
    distancePeakSpeedMPerSec(k) = changed.analyticPeakSpeedMPerSec;
    distancePeakAccelerationMPerSec2(k) = ...
        changed.analyticPeakAccelerationMPerSec2;
    distanceMinimumDurationSec(k) = changed.minimumFeasibleDurationSec;
    distanceFeasible(k) = changed.feasible;
end
figure('Name','P21 target-distance sweep');
subplot(3,1,1);
plot(targetPositionValuesM,distancePeakSpeedMPerSec,'bo-', ...
    'LineWidth',1.7);
hold on; yline(5,'r:','Speed limit'); hold off; grid on;
xlabel('Target position from zero (m)'); ylabel('Peak speed (m/s)');
title('Sweep 1 changed view: farther moves demand more speed');
subplot(3,1,2);
plot(targetPositionValuesM,distancePeakAccelerationMPerSec2,'ms-', ...
    'LineWidth',1.7);
hold on; yline(2,'r:','Acceleration limit'); hold off; grid on;
xlabel('Target position from zero (m)');
ylabel('Peak acceleration (m/s^2)');
title('The same normalized path spans more metres');
subplot(3,1,3);
plot(targetPositionValuesM,distanceMinimumDurationSec,'kd-', ...
    'LineWidth',1.7,'DisplayName','Minimum feasible duration');
hold on;
yline(8,'b:','Requested duration');
distanceFeasibleMarkersSec = 8*ones(size(targetPositionValuesM));
distanceFeasibleMarkersSec(~distanceFeasible) = NaN;
distanceInfeasibleMarkersSec = 8*ones(size(targetPositionValuesM));
distanceInfeasibleMarkersSec(distanceFeasible) = NaN;
plot(targetPositionValuesM,distanceFeasibleMarkersSec,'go', ...
    'DisplayName','Feasible request');
plot(targetPositionValuesM,distanceInfeasibleMarkersSec,'rx', ...
    'LineWidth',1.5,'DisplayName','Infeasible request');
hold off; grid on;
xlabel('Target position from zero (m)');
ylabel('Duration (s)');
title('Feasibility follows the larger exact duration bound');
legend('Location','best');

%% Explain lever 1 from distance scaling
% For fixed duration, each derivative is proportional to distance. The
% speed-derived duration bound is linear in distance, while the
% acceleration-derived bound grows with its square root. Their maximum,
% rather than their sum, is the minimum feasible duration.

%% Reset, then move lever 2: sweep only move duration
% Distance returns to 20 m; both limits and the sample count remain fixed.
% This isolates time scaling rather than mixing path and constraint changes.
moveDurationValuesSec = [4 6 8 10 12];
durationPeakSpeedMPerSec = zeros(size(moveDurationValuesSec));
durationPeakAccelerationMPerSec2 = zeros(size(moveDurationValuesSec));
durationPeakJerkMPerSec3 = zeros(size(moveDurationValuesSec));
durationFeasible = false(size(moveDurationValuesSec));
for k = 1:numel(moveDurationValuesSec)
    changed = model(20,moveDurationValuesSec(k),5,2,501);
    assert(changed.targetPositionM == 20 && ...
        changed.maximumSpeedMPerSec == 5 && ...
        changed.maximumAccelerationMPerSec2 == 2 && ...
        changed.sampleCount == 501, ...
        'Duration sweep changed a non-swept input.');
    durationPeakSpeedMPerSec(k) = changed.analyticPeakSpeedMPerSec;
    durationPeakAccelerationMPerSec2(k) = ...
        changed.analyticPeakAccelerationMPerSec2;
    durationPeakJerkMPerSec3(k) = changed.analyticPeakJerkMPerSec3;
    durationFeasible(k) = changed.feasible;
end
figure('Name','P21 move-duration sweep');
subplot(3,1,1);
plot(moveDurationValuesSec,durationPeakSpeedMPerSec,'bo-', ...
    'LineWidth',1.7);
hold on; yline(5,'r:','Speed limit'); hold off; grid on;
xlabel('Move duration (s)'); ylabel('Peak speed (m/s)');
title('Sweep 2 changed view: speed falls as 1 / duration');
subplot(3,1,2);
plot(moveDurationValuesSec,durationPeakAccelerationMPerSec2,'ms-', ...
    'LineWidth',1.7);
hold on; yline(2,'r:','Acceleration limit'); hold off; grid on;
xlabel('Move duration (s)');
ylabel('Peak acceleration (m/s^2)');
title('Acceleration falls as 1 / duration^2');
subplot(3,1,3);
plot(moveDurationValuesSec,durationPeakJerkMPerSec3,'kd-', ...
    'LineWidth',1.7,'DisplayName','Peak jerk');
hold on;
durationFeasibleJerkMarkers = durationPeakJerkMPerSec3;
durationFeasibleJerkMarkers(~durationFeasible) = NaN;
durationInfeasibleJerkMarkers = durationPeakJerkMPerSec3;
durationInfeasibleJerkMarkers(durationFeasible) = NaN;
plot(moveDurationValuesSec,durationFeasibleJerkMarkers,'go', ...
    'DisplayName','Feasible request');
plot(moveDurationValuesSec,durationInfeasibleJerkMarkers,'rx', ...
    'LineWidth',1.5,'DisplayName','Infeasible request');
hold off; grid on;
xlabel('Move duration (s)'); ylabel('Peak jerk (m/s^3)');
title('Jerk falls as 1 / duration^3');
legend('Location','best');

%% Explain lever 2 from the chain rule
% Changing T leaves h(tau) unchanged. Every time derivative contributes
% another factor of 1/T, which explains the first-, second-, and third-power
% scaling without relying on plot appearance or a trajectory toolbox.

%% Deliberately broken case: demand the same move in too little time
% The 4 s request still has smooth position, speed, and acceleration and
% exactly meets its endpoint conditions. It is nevertheless infeasible
% because both analytic peaks exceed the declared constraints.
broken = model(20,4,5,2,501);
recovered = model(20,8,5,2,501);
assert(~broken.speedFeasible && ~broken.accelerationFeasible && ...
    ~broken.feasible,'The broken request must violate both constraints.');
assert(isequaln(recovered,baseline), ...
    'Restoring duration must recover the exact baseline.');
figure('Name','P21 broken short-duration request');
subplot(2,1,1);
plot(broken.timeSec,broken.speedMPerSec,'m-','LineWidth',1.8, ...
    'DisplayName','Requested speed');
hold on;
yline(broken.maximumSpeedMPerSec,'r:','Speed limit');
hold off; grid on;
xlabel('Time (s)'); ylabel('Speed (m/s)');
title('Broken assumption: a smooth short move exceeds speed');
legend('Location','best');
subplot(2,1,2);
plot(broken.timeSec,broken.accelerationMPerSec2,'c-', ...
    'LineWidth',1.8,'DisplayName','Requested acceleration');
hold on;
yline(broken.maximumAccelerationMPerSec2,'r:', ...
    'Positive acceleration limit');
yline(-broken.maximumAccelerationMPerSec2,'r:', ...
    'Negative acceleration limit');
hold off; grid on;
xlabel('Time (s)'); ylabel('Acceleration (m/s^2)');
title('The same request also exceeds acceleration');
legend('Location','best');

%% Check, recover, and teach back
% Clear a generic run_checks function cached from another module before
% resolving P21's module-local checks on the active path.
clear run_checks;
run_checks;
% Teach back in exactly two sentences: name target, duration, and limits;
% explain the 1/T, 1/T^2, and 1/T^3 effects; then state why the smooth 4 s
% move is infeasible and why plant tracking remains a separate claim.
