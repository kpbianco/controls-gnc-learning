%% P12 - Recover from Integrator Windup
%
% Guiding question:
% What inputs, observable effects, and failure modes matter when you recover from Integrator Windup?
%
% Run one section at a time. Read the mechanism, inspect the baseline, move
% one lever, inspect its changed view, then reset before moving the next.

%% Read - saturation disconnects requested and applied PI effort
% P11 exposed the command gap created by an actuator limit. P12 adds the PI
% integral state I. Without protection, I keeps integrating error even when
% the actuator cannot apply the request. Back-calculation feeds the visible
% gap back into that state:
%   uRequested = Kp*e + I
%   uApplied   = clamp(uRequested,-uLimit,+uLimit)
%   dI/dt      = Ki*e + Kaw*(uApplied-uRequested)
% Predict which loop reverses its command first when r changes sign.
antiWindupGain = 1;                  % Kaw (1/s)
demandDurationSec = 3;               % time at unreachable r=2 (s)
tEnd = 12;                            % includes nine recovery seconds (s)
timeStepSec = 0.01;                   % held-command interval (s)
baseline = model(antiWindupGain,demandDurationSec,tEnd,timeStepSec);

%% Visualize baseline - same plant and limit, different integral memory
figure('Name','P12 baseline output');
stairs(baseline.t,baseline.reference,'k:','LineWidth',1.2, ...
    'DisplayName','Reference');
hold on;
plot(baseline.t,baseline.unprotected.plantOutput,'--','LineWidth',1.5, ...
    'DisplayName','PI without anti-windup');
plot(baseline.t,baseline.protected.plantOutput,'LineWidth',1.8, ...
    'DisplayName','PI with back-calculation');
xline(baseline.demandDurationSec,':','Demand reverses', ...
    'HandleVisibility','off');
hold off; grid on;
xlabel('Time (s)'); ylabel('Plant output y (output)');
title('Baseline: anti-windup releases stored integral effort');
legend('Location','best');

%% Changed view - see integral state and applied-command reversal
figure('Name','P12 baseline internal state and control');
subplot(2,1,1);
plot(baseline.t,baseline.unprotected.integralState,'--','LineWidth',1.4, ...
    'DisplayName','Unprotected integral state');
hold on;
plot(baseline.t,baseline.protected.integralState,'LineWidth',1.8, ...
    'DisplayName','Protected integral state');
xline(baseline.demandDurationSec,':','HandleVisibility','off');
hold off; grid on;
xlabel('Time (s)'); ylabel('Integral state I (actuator)');
title('The command-gap correction drains unavailable effort');
legend('Location','best');
subplot(2,1,2);
stairs(baseline.t,baseline.unprotected.appliedControl,'--','LineWidth',1.4, ...
    'DisplayName','Unprotected applied control');
hold on;
stairs(baseline.t,baseline.protected.appliedControl,'LineWidth',1.8, ...
    'DisplayName','Protected applied control');
plot(baseline.t,baseline.controlUpperLimit,'r:', ...
    'DisplayName','Actuator limits');
plot(baseline.t,baseline.controlLowerLimit,'r:', ...
    'HandleVisibility','off');
hold off; grid on;
xlabel('Time (s)'); ylabel('Applied control u (actuator)');
title('Stored integral effort delays the unprotected command reversal');
legend('Location','best');
fprintf(['Baseline metrics: release I unprotected %.3f actuator, protected ' ...
    '%.3f actuator; reversal delay unprotected %.2f s, protected %.2f s; ' ...
    'post-release IAE unprotected %.3f output*s, protected %.3f output*s.\n'], ...
    baseline.unprotected.integralStateAtRelease, ...
    baseline.protected.integralStateAtRelease, ...
    baseline.unprotected.reversalDelaySec, ...
    baseline.protected.reversalDelaySec, ...
    baseline.unprotected.postReleaseIntegralAbsoluteError, ...
    baseline.protected.postReleaseIntegralAbsoluteError);

%% Read and explain the baseline mechanism
% Both paths see the same error, actuator limit, and exact held-input plant.
% The unprotected integrator uses only Ki*e and stores effort the actuator
% never delivered. The protected path adds Kaw*(uApplied-uRequested). During
% positive clipping that term is negative, so it opposes windup. When the
% reference reverses, the protected command can turn negative immediately.

%% Sweep 1 - move only anti-windup gain
antiWindupGains = [0 0.25 0.5 1 2 4 8];
demandDurationSec = 3;
figure('Name','P12 sweep 1 - anti-windup gain'); hold on; grid on;
for k = 1:numel(antiWindupGains)
    changed = model(antiWindupGains(k),demandDurationSec,12,0.01);
    plot(changed.t,changed.protected.plantOutput,'LineWidth',1.2, ...
        'DisplayName',sprintf('Kaw=%.2g 1/s',changed.antiWindupGainPerSec));
end
stairs(baseline.t,baseline.reference,'k:','LineWidth',1.2, ...
    'DisplayName','Reference');
xlabel('Time (s)'); ylabel('Protected output y (output)');
title('Sweep 1: correction gain changes how quickly integral memory drains');
legend('Location','best');

%% Changed view - gain sweep recovery metrics
gainReleaseIntegral = zeros(size(antiWindupGains));
gainRecoveryError = zeros(size(antiWindupGains));
gainSettlingSec = NaN(size(antiWindupGains));
for k = 1:numel(antiWindupGains)
    changed = model(antiWindupGains(k),demandDurationSec,12,0.01);
    gainReleaseIntegral(k) = changed.protected.integralStateAtRelease;
    gainRecoveryError(k) = ...
        changed.protected.postReleaseIntegralAbsoluteError;
    gainSettlingSec(k) = changed.protected.settlingTimeSec;
end
figure('Name','P12 anti-windup gain metrics');
subplot(2,1,1);
plot(antiWindupGains,gainReleaseIntegral,'o-','LineWidth',1.4); grid on;
xlabel('Anti-windup gain Kaw (1/s)');
ylabel('Integral state at reversal (actuator)');
title('More correction removes more stored positive effort');
subplot(2,1,2);
plot(antiWindupGains,gainRecoveryError,'s-','LineWidth',1.4); grid on;
xlabel('Anti-windup gain Kaw (1/s)');
ylabel('Post-release integral absolute error (output*s)');
title('Too little leaves windup; too much can over-unwind');

%% Read and explain sweep 1
% Only Kaw moved. Kaw=0 is the exact no-protection limiting case, so the two
% paths coincide. Moderate correction lowers recovery error. Very large Kaw
% can drive I too negative during positive clipping and produce an opposite
% recovery transient. Anti-windup gain is a recovery tradeoff, not a magic
% command for the actuator to exceed its limit.

%% Sweep 2 - reset gain and move only high-demand duration
antiWindupGain = 1;
demandDurationsSec = [1 2 3 4 5];
figure('Name','P12 sweep 2 - saturation duration'); hold on; grid on;
for k = 1:numel(demandDurationsSec)
    changed = model(antiWindupGain,demandDurationsSec(k), ...
        demandDurationsSec(k)+9,0.01);
    plot(changed.t-demandDurationsSec(k), ...
        changed.unprotected.plantOutput,'--','LineWidth',1.2, ...
        'DisplayName',sprintf('unprotected, demand %.0f s', ...
        changed.demandDurationSec));
end
xline(0,':','Reference reverses','HandleVisibility','off');
xlabel('Time from reference reversal (s)');
ylabel('Unprotected output y (output)');
title('Sweep 2: longer saturation stores more unprotected integral effort');
legend('Location','best');

%% Changed view - duration sweep stored effort and recovery
durationUnprotectedIntegral = zeros(size(demandDurationsSec));
durationProtectedIntegral = zeros(size(demandDurationsSec));
durationUnprotectedError = zeros(size(demandDurationsSec));
durationProtectedError = zeros(size(demandDurationsSec));
for k = 1:numel(demandDurationsSec)
    changed = model(antiWindupGain,demandDurationsSec(k), ...
        demandDurationsSec(k)+9,0.01);
    durationUnprotectedIntegral(k) = ...
        changed.unprotected.integralStateAtRelease;
    durationProtectedIntegral(k) = ...
        changed.protected.integralStateAtRelease;
    durationUnprotectedError(k) = ...
        changed.unprotected.postReleaseIntegralAbsoluteError;
    durationProtectedError(k) = ...
        changed.protected.postReleaseIntegralAbsoluteError;
end
figure('Name','P12 demand-duration metrics');
subplot(2,1,1);
plot(demandDurationsSec,durationUnprotectedIntegral,'o--','LineWidth',1.4, ...
    'DisplayName','Unprotected');
hold on;
plot(demandDurationsSec,durationProtectedIntegral,'s-','LineWidth',1.4, ...
    'DisplayName','Protected');
hold off; grid on;
xlabel('High-demand duration (s)');
ylabel('Integral state at reversal (actuator)');
title('Unprotected memory grows while the actuator remains pinned');
legend('Location','best');
subplot(2,1,2);
plot(demandDurationsSec,durationUnprotectedError,'o--','LineWidth',1.4, ...
    'DisplayName','Unprotected');
hold on;
plot(demandDurationsSec,durationProtectedError,'s-','LineWidth',1.4, ...
    'DisplayName','Protected');
hold off; grid on;
xlabel('High-demand duration (s)');
ylabel('Post-release integral absolute error (output*s)');
title('Back-calculation bounds the recovery penalty');
legend('Location','best');

%% Read and explain sweep 2
% Kaw reset to 1 1/s. Only the time spent demanding unreachable output
% moved. Longer clipping gives the naive Ki*e integrator more time to grow.
% The protected state instead responds to the requested-applied gap already
% exposed in P11, so its release state and recovery error remain bounded.

%% Broken case - reverse the back-calculation sign
% The correct gap is uApplied-uRequested. Reversing it makes missing effort
% reinforce the integral state. This is positive feedback inside the
% anti-windup path: the request grows while the actuator remains pinned in
% the wrong direction after the reference has reversed.
broken = model(0.5,3,8,0.01,-1);
recovered = model(0.5,3,8,0.01,1);
figure('Name','P12 broken correction sign and recovery');
subplot(2,1,1);
stairs(broken.t,broken.reference,'k:','DisplayName','Reference');
hold on;
plot(broken.t,broken.protected.plantOutput,'--','LineWidth',1.6, ...
    'DisplayName','Wrong-sign correction');
plot(recovered.t,recovered.protected.plantOutput,'LineWidth',1.8, ...
    'DisplayName','Correct-sign recovery');
hold off; grid on;
xlabel('Time (s)'); ylabel('Plant output y (output)');
title('Broken sign keeps the actuator driving away from the new target');
legend('Location','best');
subplot(2,1,2);
plot(broken.t,broken.protected.integralState,'--','LineWidth',1.6, ...
    'DisplayName','Wrong-sign integral state');
hold on;
plot(recovered.t,recovered.protected.integralState,'LineWidth',1.8, ...
    'DisplayName','Correct-sign integral state');
hold off; grid on;
xlabel('Time (s)'); ylabel('Integral state I (actuator)');
title('The sign error turns unwinding feedback into runaway memory');
legend('Location','best');
fprintf(['Broken/recovered metrics: final integral %.2f / %.2f actuator; ' ...
    'post-release IAE %.2f / %.2f output*s; final error %.2f / %.2f output.\n'], ...
    broken.protected.integralState(end), ...
    recovered.protected.integralState(end), ...
    broken.protected.postReleaseIntegralAbsoluteError, ...
    recovered.protected.postReleaseIntegralAbsoluteError, ...
    broken.protected.finalTrackingError, ...
    recovered.protected.finalTrackingError);

%% Check and teach back
% Run run_checks. Then explain in two sentences: why can a PI controller keep
% commanding the old direction after the reference reverses, and how does
% back-calculation use the requested-applied command gap to recover?
run_checks;
