%% P11 - Drive an Actuator into Saturation
%
% Guiding question:
% What inputs, observable effects, and failure modes matter when you drive an Actuator into Saturation?
%
% Run one section at a time. Observe each changed view before reading the
% mechanism. Reset the first lever before moving the second.

%% Read - separate requested effort from available actuator authority
% P10 exposed computed and applied command timing. P11 fixes timing and limits
% amplitude. The controller requests u=4*(r-y), while the actuator can apply
% only values between -uLimit and +uLimit. Predict which trace clips first.
reference = 1;                        % r (output)
controlLimit = 2;                     % uLimit (actuator)
tEnd = 5;                             % observation duration (s)
timeStepSec = 0.01;                   % held-command interval (s)
baseline = model(reference,controlLimit,tEnd,timeStepSec);

%% Visualize baseline - limited and unlimited output
figure('Name','P11 baseline output');
plot(baseline.t,baseline.reference,'k:','LineWidth',1.2, ...
    'DisplayName','Reference');
hold on;
plot(baseline.t,baseline.unlimitedOutput,'--','LineWidth',1.3, ...
    'DisplayName','Unlimited actuator');
plot(baseline.t,baseline.plantOutput,'LineWidth',1.8, ...
    'DisplayName','Limited actuator');
hold off; grid on;
xlabel('Time (s)'); ylabel('Plant output y (output)');
title('Baseline: transient amplitude clipping slows the plant');
legend('Location','best');

%% Changed view - expose requested, applied, and missing command
figure('Name','P11 baseline actuator command');
subplot(2,1,1);
stairs(baseline.t,baseline.requestedControl,'--','LineWidth',1.3, ...
    'DisplayName','Requested control');
hold on;
stairs(baseline.t,baseline.appliedControl,'LineWidth',1.8, ...
    'DisplayName','Applied control');
plot(baseline.t,baseline.controlUpperLimit,'r:', ...
    'DisplayName','Positive limit');
plot(baseline.t,baseline.controlLowerLimit,'r:', ...
    'HandleVisibility','off');
hold off; grid on;
xlabel('Time (s)'); ylabel('Control command u (actuator)');
title('The actuator applies the clamp, not the full request');
legend('Location','best');
subplot(2,1,2);
stairs(baseline.t,baseline.clippingGap,'LineWidth',1.6);
grid on;
xlabel('Time (s)'); ylabel('Missing command (actuator)');
title('Requested minus applied command is the visible clipping gap');
fprintf(['Baseline metrics: r %.2f output, limit %.2f actuator, max request ' ...
    '%.2f actuator, clipped %.1f%% (%.2f s), release %.2f s, final error ' ...
    '%.4f output, integral absolute error %.4f output*s.\n'], ...
    baseline.referenceValue,baseline.controlLimit, ...
    baseline.maximumAbsRequestedControl,100*baseline.saturationFraction, ...
    baseline.saturationDurationSec,baseline.releaseTimeSec, ...
    baseline.finalTrackingError,baseline.integralAbsoluteError);

%% Read and explain the baseline mechanism
% At first, the controller requests four actuator units but only two arrive.
% With tau=1 s and g=1 output/actuator, the exact interval transition is
% yNext=exp(-dt/tau)*y+(1-exp(-dt/tau))*g*uApplied.
% Once the error shrinks enough, the request enters +/-uLimit, clipping ends,
% and the limited path approaches the same 4*r/5 P-only equilibrium.

%% Sweep 1 - move only reference amplitude
references = [0.25 0.5 1 1.5 2];
controlLimit = 2;
figure('Name','P11 sweep 1 - reference amplitude'); hold on; grid on;
for k = 1:numel(references)
    changed = model(references(k),controlLimit,5,0.01);
    plot(changed.t,changed.plantOutput,'LineWidth',1.2, ...
        'DisplayName',sprintf('r=%.2f output, clipped %.0f%%', ...
        changed.referenceValue,100*changed.saturationFraction));
end
xlabel('Time (s)'); ylabel('Plant output y (output)');
title('Sweep 1: larger commands spend longer at the same actuator limit');
legend('Location','best');

%% Changed view - reference sweep clipping metrics
referenceSaturationPercent = zeros(size(references));
referenceMissingCommand = zeros(size(references));
referenceIntegralError = zeros(size(references));
for k = 1:numel(references)
    changed = model(references(k),controlLimit,5,0.01);
    referenceSaturationPercent(k) = 100*changed.saturationFraction;
    referenceMissingCommand(k) = changed.maximumClippingGap;
    referenceIntegralError(k) = changed.integralAbsoluteError;
end
figure('Name','P11 reference sweep metrics');
subplot(2,1,1);
plot(references,referenceSaturationPercent,'o-','LineWidth',1.4); grid on;
xlabel('Reference r (output)'); ylabel('Time clipped (%)');
title('Demand amplitude controls how long authority is exhausted');
subplot(2,1,2);
plot(references,referenceMissingCommand,'s-','LineWidth',1.4); grid on;
xlabel('Reference r (output)'); ylabel('Peak missing command (actuator)');
title('Larger demand widens requested-versus-applied effort');

%% Read and explain sweep 1
% Only r moved; uLimit stayed at 2 actuator units, Kp stayed at 4, and the
% plant and time grid stayed fixed. Larger initial error requests more effort,
% so the same clamp removes more command and remains active longer.

%% Sweep 2 - reset reference and move only actuator limit
reference = 1;
controlLimits = [0.4 0.6 0.8 1.2 2];
figure('Name','P11 sweep 2 - actuator limit'); hold on; grid on;
for k = 1:numel(controlLimits)
    changed = model(reference,controlLimits(k),5,0.01);
    plot(changed.t,changed.plantOutput,'LineWidth',1.2, ...
        'DisplayName',sprintf('limit=%.1f actuator, clipped %.0f%%', ...
        changed.controlLimit,100*changed.saturationFraction));
end
plot(baseline.t,baseline.unlimitedOutput,'k--','LineWidth',1.3, ...
    'DisplayName','Unlimited actuator');
xlabel('Time (s)'); ylabel('Plant output y (output)');
title('Sweep 2: available actuator authority sets the reachable motion');
legend('Location','best');

%% Changed view - actuator-limit error and release metrics
limitSaturationPercent = zeros(size(controlLimits));
limitIntegralError = zeros(size(controlLimits));
limitReleaseTimeSec = NaN(size(controlLimits));
for k = 1:numel(controlLimits)
    changed = model(reference,controlLimits(k),5,0.01);
    limitSaturationPercent(k) = 100*changed.saturationFraction;
    limitIntegralError(k) = changed.integralAbsoluteError;
    limitReleaseTimeSec(k) = changed.releaseTimeSec;
end
figure('Name','P11 actuator-limit sweep metrics');
subplot(2,1,1);
plot(controlLimits,limitSaturationPercent,'o-','LineWidth',1.4); grid on;
xlabel('Actuator limit uLimit (actuator)'); ylabel('Time clipped (%)');
title('More authority shortens or removes saturation');
subplot(2,1,2);
plot(controlLimits,limitIntegralError,'s-','LineWidth',1.4); grid on;
xlabel('Actuator limit uLimit (actuator)');
ylabel('Integral absolute error (output*s)');
title('Missing effort accumulates as tracking error, not integral state');

%% Read and explain sweep 2
% r reset to 1 output. Only uLimit moved. Limits at or below the unlimited
% equilibrium command of 0.8 actuator remain clipped over the finite view;
% higher limits release sooner. No integrator exists in this lesson, so this
% error metric must not be confused with controller windup.

%% Broken case - demand more output than maximum actuation can support
% With r=1.5 output and uLimit=0.6 actuator, even constant maximum command
% can only approach y=0.6 output. The controller keeps requesting more, the
% command gap never closes, and the target is physically infeasible.
broken = model(1.5,0.6,5,0.01);
recovered = model(1.5,2,5,0.01);
figure('Name','P11 broken authority and recovery');
subplot(2,1,1);
plot(broken.t,broken.reference,'k:','DisplayName','Reference');
hold on;
plot(broken.t,broken.plantOutput,'LineWidth',1.7, ...
    'DisplayName','Broken output');
plot(recovered.t,recovered.plantOutput,'LineWidth',1.7, ...
    'DisplayName','Recovered output');
hold off; grid on;
xlabel('Time (s)'); ylabel('Plant output y (output)');
title('Broken authority leaves the output far below the reference');
legend('Location','best');
subplot(2,1,2);
stairs(broken.t,broken.requestedControl,'--','LineWidth',1.2, ...
    'DisplayName','Broken request');
hold on;
stairs(broken.t,broken.appliedControl,'LineWidth',1.7, ...
    'DisplayName','Broken applied');
stairs(recovered.t,recovered.appliedControl,'LineWidth',1.7, ...
    'DisplayName','Recovered applied');
hold off; grid on;
xlabel('Time (s)'); ylabel('Control command u (actuator)');
title('Recovery changes only the actuator limit from 0.6 to 2');
legend('Location','best');
fprintf(['Broken: clipped %.0f%%, final error %.3f output; recovery: clipped ' ...
    '%.0f%%, release %.2f s, final error %.3f output.\n'], ...
    100*broken.saturationFraction,broken.finalTrackingError, ...
    100*recovered.saturationFraction,recovered.releaseTimeSec, ...
    recovered.finalTrackingError);

%% Read and explain recovery
% The failure violates the assumption that the actuator can supply the effort
% needed by the demanded motion. Increasing only uLimit lets the applied
% command meet the request after a transient. Lowering the reference would be
% another honest recovery; relabeling or smoothing the clipped trace would not.
