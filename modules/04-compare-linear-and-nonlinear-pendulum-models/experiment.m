%% P04 - Compare Linear and Nonlinear Pendulum Models
%
% Guiding question:
% What inputs, observable effects, and failure modes matter when you compare Linear and Nonlinear Pendulum Models?
%
% Run one section at a time. Observe the changed view before reading its
% mechanism, and reset each lever before moving the next one.

%% Read - one physical pendulum, two restoring laws
% P03 showed how a linear second-order equation maps to oscillatory motion.
% Here both predictions start from the same state. The nonlinear model keeps
% sin(theta); the linear model assumes sin(theta) is approximately theta.
% Predict whether that substitution makes a visible difference at 20 deg.
initialAngleDeg = 20;    % release angle (deg)
initialRateDegPerSec = 0;% release angular rate (deg/s)
lengthM = 1;             % pendulum length (m)
dampingRatio = 0.02;     % linearized damping ratio (dimensionless)
tEnd = 12;               % observation duration (s)
dt = 0.01;               % calculation interval (s)
baseline = model(initialAngleDeg,initialRateDegPerSec,lengthM, ...
    dampingRatio,tEnd,dt);

%% Visualize baseline - compare angle histories from the same release
figure('Name','P04 baseline angle comparison');
plot(baseline.t,baseline.linearAngleDeg,'--','LineWidth',1.3, ...
    'DisplayName','Linear: theta restoring term');
hold on;
plot(baseline.t,baseline.nonlinearAngleDeg,'LineWidth',1.5, ...
    'DisplayName','Nonlinear: sin(theta) restoring term');
hold off; grid on;
xlabel('Time (s)'); ylabel('Angle theta (deg)');
title('Baseline: equal initial state, slightly different cycle timing');
legend('Location','northeast');

fprintf(['Baseline metrics: wn = %.3f (rad/s), small-angle period = %.3f s, ' ...
    'max angle difference = %.3f deg, nonlinear zero-crossing delay = %.2f%%.\n'], ...
    baseline.naturalFrequencyRadPerSec,baseline.smallAnglePeriodSec, ...
    baseline.maxAbsErrorDeg,baseline.nonlinearZeroDelayPercent);

%% Changed view - expose the restoring-law mechanism
figure('Name','P04 restoring-law comparison');
plot(baseline.restoringAngleRad*180/pi, ...
    baseline.linearRestoringAccelerationRadPerSec2,'--','LineWidth',1.3, ...
    'DisplayName','Linear -g theta/L');
hold on;
plot(baseline.restoringAngleRad*180/pi, ...
    baseline.nonlinearRestoringAccelerationRadPerSec2,'LineWidth',1.5, ...
    'DisplayName','Nonlinear -g sin(theta)/L');
hold off; grid on;
xlabel('Angle theta (deg)');
ylabel('Restoring angular acceleration (rad/s^2)');
title('The approximation error is small near theta = 0 and grows outward');
legend('Location','best');

%% Read and explain the baseline mechanism
% Near zero, sin(theta) and theta have nearly the same slope. Away from
% zero, |sin(theta)| < |theta|, so the nonlinear pendulum is restored less
% aggressively. Its zero crossing arrives later and phase error accumulates.

%% Sweep 1 - move only the release angle
releaseAnglesDeg = [5 30 90];
figure('Name','P04 sweep 1 - release angle error'); hold on; grid on;
for k = 1:numel(releaseAnglesDeg)
    changed = model(releaseAnglesDeg(k),initialRateDegPerSec,lengthM, ...
        dampingRatio,tEnd,dt);
    plot(changed.t,changed.angleErrorDeg,'LineWidth',1.3,'DisplayName', ...
        sprintf('theta_0 = %g deg, max |error| = %.1f deg', ...
        releaseAnglesDeg(k),changed.maxAbsErrorDeg));
end
xlabel('Time (s)'); ylabel('Nonlinear - linear angle (deg)');
title('Sweep 1: larger release angle amplifies approximation error');
legend('Location','best');

%% Read and explain sweep 1
% Only release angle moved. Length, damping, and initial rate stayed fixed.
% Five degrees keeps sin(theta) close to theta; ninety degrees exposes a
% weaker nonlinear restoring term and a large timing mismatch.

%% Sweep 2 - reset release angle and move only pendulum length
lengthsM = [0.5 1 2];
figure('Name','P04 sweep 2 - pendulum length'); hold on; grid on;
for k = 1:numel(lengthsM)
    changed = model(initialAngleDeg,initialRateDegPerSec,lengthsM(k), ...
        dampingRatio,tEnd,dt);
    plot(changed.t,changed.nonlinearAngleDeg,'LineWidth',1.3, ...
        'DisplayName',sprintf('L = %.1f m, T_small = %.2f s', ...
        lengthsM(k),changed.smallAnglePeriodSec));
end
xlabel('Time (s)'); ylabel('Nonlinear angle theta (deg)');
title('Sweep 2: longer pendulums oscillate more slowly');
legend('Location','northeast');

%% Read and explain sweep 2
% Release angle reset to 20 deg. Only L moved, so wn = sqrt(g/L) changes.
% Increasing length weakens angular restoring acceleration and stretches the
% time scale in both models; it does not repair the angle approximation.

%% Broken case - trust the small-angle model after a 120 degree release
% The violated assumption is |theta| << 1 rad. At 120 deg, theta is 2.094
% rad while sin(theta) is only 0.866. The linear model therefore invents a
% much stronger restoring acceleration and predicts an early crossing.
broken = model(120,0,lengthM,dampingRatio,tEnd,dt);
recovered = model(5,0,lengthM,dampingRatio,tEnd,dt);
figure('Name','P04 broken and recovered approximation');
subplot(2,1,1);
plot(broken.t,broken.linearAngleDeg,'--','LineWidth',1.3, ...
    'DisplayName','Broken use: linear at 120 deg');
hold on;
plot(broken.t,broken.nonlinearAngleDeg,'LineWidth',1.5, ...
    'DisplayName','Reference: nonlinear at 120 deg');
hold off; grid on;
xlabel('Time (s)'); ylabel('Angle theta (deg)');
title('Broken assumption: the large-angle linear prediction runs ahead');
legend('Location','best');

subplot(2,1,2);
plot(recovered.t,recovered.linearAngleDeg,'--','LineWidth',1.3, ...
    'DisplayName','Linear at 5 deg');
hold on;
plot(recovered.t,recovered.nonlinearAngleDeg,'LineWidth',1.5, ...
    'DisplayName','Nonlinear at 5 deg');
hold off; grid on;
xlabel('Time (s)'); ylabel('Angle theta (deg)');
title('Recovery: reduce the release angle and the models overlap');
legend('Location','best');

fprintf(['Broken-case metric: first-zero delay = %.1f%% and max angle difference = %.1f deg. ' ...
    'At 5 deg, max difference falls to %.3f deg.\n'], ...
    broken.nonlinearZeroDelayPercent,broken.maxAbsErrorDeg, ...
    recovered.maxAbsErrorDeg);

%% Read and explain recovery
% The linear equation itself did not become unstable; it was applied outside
% its approximation region. Reducing the release angle restores agreement.
% When large-angle timing matters, retain sin(theta) instead of forcing the
% linear model to answer a question it was not built to answer.
