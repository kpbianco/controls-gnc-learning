%% P06 - Tune a PID by Observing Each Term
%
% Guiding question:
% What inputs, observable effects, and failure modes matter when you tune a PID by Observing Each Term?
%
% Run one section at a time. Observe each changed view before reading its
% mechanism, and reset the first lever before moving the second.

%% Read - connect P05 feedback to three visible force terms
% P05 showed u = Kp*e. Here a damped 1 kg carriage must reach 1 m while a
% constant -1 N load pulls backward. The PID force is
% u = Kp*e + Ki*q - Kd*v, with q' = e and e' = -v.
% Predict which term remains nonzero after both error and velocity approach zero.
proportionalGain = 4;  % Kp (N/m)
integralGain = 1;      % Ki (N/(m*s))
derivativeGain = 3;    % Kd (N*s/m)
loadForceN = -1;       % constant external load (N)
derivativeSign = -1;   % -1 makes derivative oppose velocity
tEnd = 20;             % observation duration (s)
dt = 0.01;             % requested calculation interval (s)
baseline = model(proportionalGain,integralGain,derivativeGain, ...
    loadForceN,derivativeSign,tEnd,dt);

%% Visualize baseline - reference and carriage position
figure('Name','P06 baseline position');
plot(baseline.t,baseline.referenceM*ones(size(baseline.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
hold on;
plot(baseline.t,baseline.positionM,'LineWidth',1.5, ...
    'DisplayName','Carriage position x');
hold off; grid on;
xlabel('Time (s)'); ylabel('Position x (m)');
title('Baseline: PID rejects a constant load');
legend('Location','southeast');
fprintf(['Baseline metrics: final error = %.5f m, overshoot = %.4f m, ' ...
    'settling time = %.2f s, max |u| = %.2f N.\n'], ...
    baseline.finalTrackingErrorM,baseline.overshootM, ...
    baseline.settlingTimeSec,baseline.maxAbsControlN);

%% Changed view - observe P, I, and D separately
figure('Name','P06 baseline PID terms');
plot(baseline.t,baseline.proportionalControlN,'LineWidth',1.3, ...
    'DisplayName','P = Kp e');
hold on;
plot(baseline.t,baseline.integralControlN,'LineWidth',1.3, ...
    'DisplayName','I = Ki q');
plot(baseline.t,baseline.derivativeControlN,'LineWidth',1.3, ...
    'DisplayName','D = -Kd v');
plot(baseline.t,baseline.totalControlN,'k','LineWidth',1.5, ...
    'DisplayName','Total u');
hold off; grid on;
xlabel('Time (s)'); ylabel('Controller force (N)');
title('Each term acts on a different signal');
legend('Location','best');

%% Read and explain the baseline mechanism
% P reacts immediately to present error, so P(0) = 4 N. I starts at zero,
% accumulates the error history, and approaches +1 N to oppose the -1 N load.
% D starts at zero because the carriage is at rest, then opposes velocity.
% Derivative-on-measurement avoids a force impulse from the reference step.

%% Sweep 1 - move only integral gain
integralGains = [0 0.5 2];
figure('Name','P06 sweep 1 - integral gain'); hold on; grid on;
for k = 1:numel(integralGains)
    changed = model(proportionalGain,integralGains(k),derivativeGain, ...
        loadForceN,-1,tEnd,dt);
    plot(changed.t,changed.positionM,'LineWidth',1.3,'DisplayName', ...
        sprintf('Ki = %.1f, final e = %.3f m, overshoot = %.3f m', ...
        integralGains(k),changed.finalTrackingErrorM,changed.overshootM));
end
plot(baseline.t,baseline.referenceM*ones(size(baseline.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
xlabel('Time (s)'); ylabel('Position x (m)');
title('Sweep 1: integral memory removes load offset but can overshoot');
legend('Location','southeast');

%% Read and explain sweep 1
% Only Ki moved; Kp, Kd, load, derivative sign, duration, and interval stayed
% fixed. Ki = 0 leaves the independently predicted error -Fload/Kp = 0.25 m.
% More Ki builds holding force sooner, but too much stored correction carries
% the carriage past the reference before the error history unwinds.

%% Sweep 2 - reset integral gain and move only derivative gain
derivativeGains = [0 1.5 3];
figure('Name','P06 sweep 2 - derivative gain'); hold on; grid on;
for k = 1:numel(derivativeGains)
    changed = model(proportionalGain,integralGain,derivativeGains(k), ...
        loadForceN,-1,tEnd,dt);
    plot(changed.t,changed.positionM,'LineWidth',1.3,'DisplayName', ...
        sprintf('Kd = %.1f, overshoot = %.3f m, max |D| = %.2f N', ...
        derivativeGains(k),changed.overshootM, ...
        changed.maxAbsDerivativeControlN));
end
plot(baseline.t,baseline.referenceM*ones(size(baseline.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
xlabel('Time (s)'); ylabel('Position x (m)');
title('Sweep 2: derivative force trades effort for damping');
legend('Location','southeast');

%% Read and explain sweep 2
% Ki reset to 1. Only Kd moved. With Kd = 0 the lightly damped carriage
% overshoots. Larger Kd produces a force opposite velocity, reducing overshoot
% while increasing the peak derivative contribution. It does not supply the
% steady +1 N load force because velocity approaches zero.

%% Broken case - reinforce velocity instead of opposing it
% The violated assumption is derivative polarity: the D term must remove
% motion energy. derivativeSign = +1 makes D = +Kd*v, so the controller pushes
% in the direction of motion and creates negative effective damping.
broken = model(4,0.5,3,-1,1,4,0.01);
recovered = model(4,0.5,3,-1,-1,4,0.01);
figure('Name','P06 broken and recovered derivative sign');
subplot(2,1,1);
plot(broken.t,broken.positionM,'LineWidth',1.5, ...
    'DisplayName','Broken: D reinforces velocity');
hold on;
plot(broken.t,broken.referenceM*ones(size(broken.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
hold off; grid on;
xlabel('Time (s)'); ylabel('Position x (m)');
title('Broken derivative sign: growing oscillation');
legend('Location','best');
subplot(2,1,2);
plot(recovered.t,recovered.positionM,'LineWidth',1.5, ...
    'DisplayName','Recovered: D opposes velocity');
hold on;
plot(recovered.t,recovered.referenceM*ones(size(recovered.t)),'k:', ...
    'LineWidth',1.2,'DisplayName','Reference r');
hold off; grid on;
xlabel('Time (s)'); ylabel('Position x (m)');
title('Recovery: restore damping before retuning');
legend('Location','southeast');
fprintf(['Broken metric: effective damping = %.1f N*s/m, max |x| = %.1f m. ' ...
    'Recovered effective damping = %.1f N*s/m, max |x| = %.2f m.\n'], ...
    broken.effectiveDampingNPerMPerSec,max(abs(broken.positionM)), ...
    recovered.effectiveDampingNPerMPerSec,max(abs(recovered.positionM)));

%% Read and explain recovery
% This symptom is not ordinary integral overshoot. The wrong D sign adds
% energy whenever the carriage moves. Restore D = -Kd*v first; only after the
% loop is damping motion does changing gain become a meaningful tuning action.
