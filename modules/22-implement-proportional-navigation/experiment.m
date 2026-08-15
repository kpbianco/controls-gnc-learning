%% Read: proportional navigation turns line-of-sight motion into acceleration
% P21 generated a feasible reference before asking a plant to follow it.
% P22 now closes a guidance loop around relative geometry. If r is the
% target-to-interceptor relative position and v_rel its derivative, then
% closing speed Vc and line-of-sight rate lambdaDot are computed directly.
% The transparent command is a_cmd = N*max(Vc,0)*lambdaDot.

%% Make one prediction before the baseline
% For N=3, will the line of sight keep rotating, or settle toward a
% collision course before the interceptor reaches the crossing target?

%% Visualize the deterministic baseline
baseline = model(3,60,80,0.02,25);
fprintf(['Baseline: %s at %.2f s, closest range %.3f m, peak command ' ...
    '%.3f m/s^2, LOS-rate ratio %.5f, saturation %.2f s.\n'], ...
    baseline.terminationReason,baseline.closestApproachTimeSec, ...
    baseline.closestApproachDistanceM, ...
    baseline.peakCommandAccelerationMPerSec2, ...
    baseline.lineOfSightRateReductionRatio, ...
    baseline.saturationDurationSec);

figure('Name','P22 baseline engagement geometry');
plot(baseline.interceptorXM,baseline.interceptorYM,'b-', ...
    'LineWidth',1.8,'DisplayName','Interceptor');
hold on;
plot(baseline.targetXM,baseline.targetYM,'m--', ...
    'LineWidth',1.8,'DisplayName','Target');
plot(baseline.interceptorXM(1),baseline.interceptorYM(1),'bo', ...
    'DisplayName','Interceptor start');
plot(baseline.targetXM(1),baseline.targetYM(1),'ms', ...
    'DisplayName','Target start');
plot(baseline.interceptorXM(end),baseline.interceptorYM(end),'gx', ...
    'LineWidth',2,'DisplayName','Terminal separation');
axis equal; grid on;
xlabel('Downrange x (m)'); ylabel('Crossrange y (m)');
title('Baseline: PN bends the interceptor toward a collision course');
legend('Location','best');

figure('Name','P22 baseline LOS and acceleration');
subplot(3,1,1);
plot(baseline.timeSec,baseline.rangeM,'k-','LineWidth',1.7);
hold on; yline(baseline.interceptRadiusM,'g:','Intercept radius');
hold off; grid on;
xlabel('Time (s)'); ylabel('Range (m)');
title('Range closes to the declared intercept radius');
subplot(3,1,2);
plot(baseline.timeSec,rad2deg(baseline.lineOfSightRateRadPerSec), ...
    'c-','LineWidth',1.7);
hold on; yline(0,'k:','Constant-bearing condition'); hold off; grid on;
xlabel('Time (s)'); ylabel('LOS rate (deg/s)');
title('Complementary view: PN drives LOS rotation toward zero');
subplot(3,1,3);
plot(baseline.timeSec,baseline.commandAccelerationMPerSec2,'m--', ...
    'LineWidth',1.5,'DisplayName','Commanded acceleration');
hold on;
plot(baseline.timeSec,baseline.actualAccelerationMPerSec2,'b-', ...
    'LineWidth',1.7,'DisplayName','Applied acceleration');
yline(baseline.maximumAccelerationMPerSec2,'r:', ...
    'Positive acceleration limit');
yline(-baseline.maximumAccelerationMPerSec2,'r:', ...
    'Negative acceleration limit');
hold off; grid on;
xlabel('Time (s)'); ylabel('Lateral acceleration (m/s^2)');
title('Baseline command remains inside acceleration authority');
legend('Location','best');

%% Read the mechanism: constant bearing, decreasing range
% The cross product r_x*v_rel_y-r_y*v_rel_x divided by range squared is
% lambdaDot. The negative relative radial velocity is Vc. With positive Vc,
% PN commands normal acceleration proportional to LOS rotation; as the
% collision course forms, lambdaDot and the required command decrease.

%% Move lever 1: sweep only navigation constant N
% Crossing speed, acceleration authority, step, and horizon reset on every
% call. N=1 reacts too weakly here; larger N removes LOS rotation sooner but
% asks for a larger initial acceleration.
navigationConstantValues = [1 2 3 4 5];
navigationMissDistanceM = zeros(size(navigationConstantValues));
navigationInitialCommandMPerSec2 = zeros(size(navigationConstantValues));
navigationInterceptTimeSec = NaN(size(navigationConstantValues));
navigationIntercepted = false(size(navigationConstantValues));
for k = 1:numel(navigationConstantValues)
    changed = model(navigationConstantValues(k),60,80,0.02,25);
    assert(changed.targetCrossingSpeedMPerSec == 60 && ...
        changed.maximumAccelerationMPerSec2 == 80 && ...
        changed.timeStepSec == 0.02 && changed.maximumTimeSec == 25, ...
        'Navigation-constant sweep changed a non-swept input.');
    navigationMissDistanceM(k) = changed.closestApproachDistanceM;
    navigationInitialCommandMPerSec2(k) = ...
        abs(changed.commandAccelerationMPerSec2(1));
    navigationIntercepted(k) = changed.intercepted;
    if changed.intercepted
        navigationInterceptTimeSec(k) = changed.closestApproachTimeSec;
    end
end
figure('Name','P22 navigation-constant sweep');
subplot(3,1,1);
semilogy(navigationConstantValues,navigationMissDistanceM,'bo-', ...
    'LineWidth',1.7);
hold on; yline(5,'g:','Intercept radius'); hold off; grid on;
xlabel('Navigation constant N (dimensionless)');
ylabel('Closest range (m)');
title('Sweep 1 changed view: too little guidance leaves a miss');
subplot(3,1,2);
plot(navigationConstantValues,navigationInitialCommandMPerSec2,'ms-', ...
    'LineWidth',1.7);
hold on; yline(80,'r:','Acceleration limit'); hold off; grid on;
xlabel('Navigation constant N (dimensionless)');
ylabel('Initial command (m/s^2)');
title('Higher N reacts harder to the same initial LOS motion');
subplot(3,1,3);
plot(navigationConstantValues,navigationInterceptTimeSec,'gd-', ...
    'LineWidth',1.7,'DisplayName','Intercept time');
hold on;
missMarkersSec = 25*ones(size(navigationConstantValues));
missMarkersSec(navigationIntercepted) = NaN;
plot(navigationConstantValues,missMarkersSec,'rx','LineWidth',1.8, ...
    'DisplayName','Time-limit miss');
hold off; grid on;
xlabel('Navigation constant N (dimensionless)');
ylabel('Event time (s)');
title('Intercept or bounded time-limit outcome');
legend('Location','best');

%% Explain lever 1 from the PN law
% At the shared initial geometry, Vc and lambdaDot are identical for every
% run, so initial command scales exactly with N. The later paths differ
% because each command changes heading and therefore future relative motion.

%% Reset, then move lever 2: sweep only acceleration authority
% N returns to 3. Reducing the actuator limit does not change the PN request;
% it clips the applied turn, allowing LOS rotation and miss distance to grow.
accelerationLimitValuesMPerSec2 = [5 10 20 40 80];
authorityMissDistanceM = zeros(size(accelerationLimitValuesMPerSec2));
authorityPeakAppliedMPerSec2 = zeros(size(accelerationLimitValuesMPerSec2));
authoritySaturationDurationSec = zeros( ...
    size(accelerationLimitValuesMPerSec2));
authorityIntercepted = false(size(accelerationLimitValuesMPerSec2));
for k = 1:numel(accelerationLimitValuesMPerSec2)
    changed = model(3,60,accelerationLimitValuesMPerSec2(k),0.02,25);
    assert(changed.navigationConstant == 3 && ...
        changed.targetCrossingSpeedMPerSec == 60 && ...
        changed.timeStepSec == 0.02 && changed.maximumTimeSec == 25, ...
        'Acceleration-authority sweep changed a non-swept input.');
    authorityMissDistanceM(k) = changed.closestApproachDistanceM;
    authorityPeakAppliedMPerSec2(k) = ...
        changed.peakActualAccelerationMPerSec2;
    authoritySaturationDurationSec(k) = changed.saturationDurationSec;
    authorityIntercepted(k) = changed.intercepted;
end
figure('Name','P22 acceleration-authority sweep');
subplot(3,1,1);
semilogy(accelerationLimitValuesMPerSec2,authorityMissDistanceM,'bo-', ...
    'LineWidth',1.7);
hold on; yline(5,'g:','Intercept radius'); hold off; grid on;
xlabel('Acceleration limit (m/s^2)'); ylabel('Closest range (m)');
title('Sweep 2 changed view: insufficient turn authority misses');
subplot(3,1,2);
plot(accelerationLimitValuesMPerSec2, ...
    authorityPeakAppliedMPerSec2,'ms-','LineWidth',1.7);
grid on;
xlabel('Acceleration limit (m/s^2)');
ylabel('Peak applied acceleration (m/s^2)');
title('Applied acceleration is explicitly clipped');
subplot(3,1,3);
plot(accelerationLimitValuesMPerSec2, ...
    authoritySaturationDurationSec,'kd-','LineWidth',1.7);
hold on;
interceptMarkersSec = authoritySaturationDurationSec;
interceptMarkersSec(~authorityIntercepted) = NaN;
plot(accelerationLimitValuesMPerSec2,interceptMarkersSec,'go', ...
    'DisplayName','Intercept');
missSaturationMarkersSec = authoritySaturationDurationSec;
missSaturationMarkersSec(authorityIntercepted) = NaN;
plot(accelerationLimitValuesMPerSec2,missSaturationMarkersSec,'rx', ...
    'LineWidth',1.8,'DisplayName','Miss');
hold off; grid on;
xlabel('Acceleration limit (m/s^2)');
ylabel('Saturation duration (s)');
title('Sustained clipping reveals the violated actuator assumption');
legend('Location','best');

%% Explain lever 2 from command-versus-applied acceleration
% PN computes a guidance command; the vehicle can only apply a bounded
% normal acceleration. A long interval where command and applied values
% differ is a physical failure symptom, not a plotting or solver artifact.

%% Deliberately broken case: assume an underpowered actuator follows PN
% Keeping N=3 but limiting acceleration to 5 m/s^2 clips the turn for most
% of the engagement. Range later opens, the horizon expires, and the miss is
% hundreds of metres even though the unsaturated guidance equation is intact.
broken = model(3,60,5,0.02,25);
recovered = model(3,60,80,0.02,25);
assert(~broken.intercepted && strcmp(broken.terminationReason,'time-limit') ...
    && broken.saturationDurationSec > 0, ...
    'The broken actuator case must saturate and miss by the time limit.');
assert(isequaln(recovered,baseline), ...
    'A fresh valid call must recover the exact baseline after the miss.');
figure('Name','P22 broken acceleration-authority case');
subplot(2,1,1);
plot(broken.timeSec,broken.rangeM,'k-','LineWidth',1.8);
hold on; yline(broken.interceptRadiusM,'g:','Intercept radius');
hold off; grid on;
xlabel('Time (s)'); ylabel('Range (m)');
title('Broken assumption: range bottoms out, then opens');
subplot(2,1,2);
plot(broken.timeSec,broken.commandAccelerationMPerSec2,'m--', ...
    'LineWidth',1.5,'DisplayName','Commanded acceleration');
hold on;
plot(broken.timeSec,broken.actualAccelerationMPerSec2,'b-', ...
    'LineWidth',1.7,'DisplayName','Applied acceleration');
yline(5,'r:','Positive acceleration limit');
yline(-5,'r:','Negative acceleration limit');
hold off; grid on;
xlabel('Time (s)'); ylabel('Lateral acceleration (m/s^2)');
title('Recognizable symptom: sustained command clipping');
legend('Location','best');

%% Check, recover, and teach back
% Clear a generic run_checks function cached from another module before
% resolving P22's module-local checks on the active path.
clear run_checks;
run_checks;
% Teach back in exactly two sentences: name relative geometry, Vc,
% lambdaDot, N, and acceleration authority; then explain why constant
% bearing plus decreasing range indicates intercept and why clipping breaks it.
